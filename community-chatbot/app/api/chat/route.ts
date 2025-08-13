import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";
import { db } from "@/app/firebase/config";
import { collection, addDoc, doc, setDoc, Timestamp } from "firebase/firestore";

// Allow streaming responses up to 120 seconds
export const maxDuration = 120;

// Backend service URLs
const BACKEND_SERVICES = {
  slack: process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000",
  jira: process.env.JIRA_SERVICE_URL || "http://localhost:8001",
  github: process.env.GITHUB_SERVICE_URL || "http://localhost:8003",
};

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatRequest {
  messages: ChatMessage[];
  mode?: string;
  conversationId?: string;
  userId?: string;
}

export async function POST(req: Request) {
  try {
    const { messages, mode = "general", conversationId, userId }: ChatRequest = await req.json();

    // Validate required fields
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response("Invalid messages format", { status: 400 });
    }

    // Get the latest user message
    const lastMessage = messages[messages.length - 1];

    if (!lastMessage || lastMessage.role !== "user") {
      return new Response("Invalid message format - last message must be from user", { status: 400 });
    }

    // Handle different integration modes
    let result;
    try {
      switch (mode) {
        case "slack":
          result = await handleSlackRequest(lastMessage.content, messages);
          break;

        case "jira":
          result = await handleJiraRequest(lastMessage.content, messages);
          break;

        case "github":
          result = await handleGitHubRequest(lastMessage.content, messages);
          break;

        default:
          result = await handleGeneralRequest(messages);
      }
    } catch (integrationError) {
      console.error(`${mode} integration error:`, integrationError);
      result = await handleGeneralRequest([
        {
          id: "fallback",
          role: "user",
          content: `I was trying to use the ${mode} integration but it seems to be unavailable. Can you help me with: ${lastMessage.content}`
        }
      ]);
    }

    // Save user message to Firestore
    if (conversationId && userId) {
      saveMessageToFirestore(conversationId, userId, lastMessage).catch(error => {
        console.error("Failed to save message to Firestore:", error);
      });
    }

    return result;
  } catch (error) {
    console.error("Chat API error:", error);
    return new Response(
      JSON.stringify({ error: "Internal Server Error" }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
}

async function saveMessageToFirestore(conversationId: string, userId: string, message: ChatMessage) {
  try {
    // Save to the conversation's messages array (simpler structure)
    const conversationRef = doc(db, "conversations", conversationId);

    const messagesRef = collection(conversationRef, "messages");
    await addDoc(messagesRef, {
      ...message,
      timestamp: Timestamp.now(),
      userId: userId,
    });
  } catch (error) {
    console.error("Firestore save error:", error);
    throw error;
  }
}

async function handleSlackRequest(message: string, messages: ChatMessage[]) {
  try {
    // Add timeout to prevent hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000 * 12);

    const response = await fetch(`${BACKEND_SERVICES.slack}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        conversation_id: "frontend-session",
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Slack API error: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();

    // Validate response structure
    if (!data || typeof data.response !== 'string') {
      throw new Error('Invalid response format from Slack service');
    }

    // Return a streaming response with the Slack agent's response
    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a Slack integration assistant. Present the information from the Slack service clearly and helpfully. If the response contains data or structured information, format it nicely for the user.",
        },
        {
          role: "user",
          content: `Based on the Slack query "${message}", here's the information I found: ${data.response}`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error("Slack integration error:", error);

    // Provide more specific error messages
    let errorMessage = "There was an error connecting to the Slack service.";
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        errorMessage = "The Slack service is taking too long to respond. Please try again.";
      } else if (error.message.includes('fetch')) {
        errorMessage = "Cannot connect to the Slack service. Please ensure it's running and accessible.";
      }
    }

    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant explaining a service connection issue. Be empathetic and provide actionable advice.",
        },
        {
          role: "user",
          content: `${errorMessage} You can try again later or switch to the General Assistant mode for general Mifos questions.`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  }
}

async function handleJiraRequest(message: string, messages: ChatMessage[]) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000 * 12);

    const response = await fetch(`${BACKEND_SERVICES.jira}/jira/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: message,
        use_fallback: true,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Jira API error: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();

    if (!data || typeof data.response !== 'string') {
      throw new Error('Invalid response format from Jira service');
    }

    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a Jira integration assistant. Present ticket information, project data, and issue details clearly. Format any structured data like ticket lists or status information in a readable way.",
        },
        {
          role: "user",
          content: `Based on the Jira query "${message}", here's what I found: ${data.response}`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error("Jira integration error:", error);

    let errorMessage = "The Jira integration service is currently unavailable.";
    if (error instanceof Error && error.name === 'AbortError') {
      errorMessage = "The Jira service is taking too long to respond.";
    }

    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant explaining service availability issues.",
        },
        {
          role: "user",
          content: `${errorMessage} Please ensure the Jira backend service is running on ${BACKEND_SERVICES.jira} or contact your administrator. You can use the General Assistant for other questions.`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  }
}

async function handleGitHubRequest(message: string, messages: ChatMessage[]) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000 * 12);

    const response = await fetch(`${BACKEND_SERVICES.github}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        session_id: "frontend-session",
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();

    if (!data || typeof data.response !== 'string') {
      throw new Error('Invalid response format from GitHub service');
    }

    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a GitHub integration assistant. Present repository information, pull request details, issue data, and code-related information clearly. Format code snippets and technical information appropriately.",
        },
        {
          role: "user",
          content: `Based on the GitHub query "${message}", here's the information: ${data.response}`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error("GitHub integration error:", error);

    let errorMessage = "The GitHub integration service is currently unavailable.";
    if (error instanceof Error && error.name === 'AbortError') {
      errorMessage = "The GitHub service is taking too long to respond.";
    }

    const result = streamText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant explaining service availability issues.",
        },
        {
          role: "user",
          content: `${errorMessage} Please ensure the GitHub backend service is running on ${BACKEND_SERVICES.github} or contact your administrator. You can use the General Assistant for other questions.`,
        },
      ],
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  }
}

async function handleGeneralRequest(messages: ChatMessage[]) {
  try {
    const result = streamText({
      model: openai("gpt-4o"),
      system: `You are a helpful Mifos Community assistant. You can help with general questions about Mifos features, documentation, and community support. 
      
      You can also guide users to use the specialized assistants:
      - **Slack Assistant**: For Slack channel management, user details, message searches, and workspace administration
      - **Jira Assistant**: For ticket status checks, issue creation, project tracking, and generating reports  
      - **GitHub Assistant**: For pull request reviews, issue tracking, repository management, and code collaboration
      
      If a user asks about Slack, Jira, or GitHub specific tasks, suggest they switch to the appropriate specialized assistant mode using the mode selector above the chat.
      
      Be helpful, friendly, and provide accurate information about Mifos platform features and capabilities.`,
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
    });

    return new Response(result.textStream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error("General request error:", error);
    throw error;
  }
}