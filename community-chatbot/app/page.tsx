"use client";

import React, { useEffect, useRef, useState } from "react";
import { Sidebar } from "@/components/chatbot/Sidebar";
import { ChatHeader } from "@/components/chatbot/ChatHeader";
import { ModeSelector } from "@/components/chatbot/ModeSelector";
import { ChatPanel } from "@/components/chatbot/ChatPanel";
import { MessageInput } from "@/components/chatbot/MessageInput";
import type { ChatHistoryItem, IntegrationMode, MessageItem } from "@/components/chatbot/types";
import {
  collection,
  getDocs,
  addDoc,
  updateDoc,
  doc as firestoreDoc,
  deleteDoc,
  query,
  where,
} from "firebase/firestore";
import { db } from "@/app/firebase/config";
import { getAuth, onAuthStateChanged } from "firebase/auth";

// Integration Modes (config)
const integrationModes: IntegrationMode[] = [
  {
    id: "general",
    name: "General Assistant",
    icon: "🤖",
    image: "/mifos.png",
    color: "bg-blue-600 hover:bg-blue-700 text-white",
    description: "Ask about features, documentation, or community",
    systemPrompt:
      "You are a helpful Mifos Community assistant. Help with general questions about Mifos features, documentation, and community support.",
  },
  {
    id: "slack",
    name: "Slack Assistant",
    icon: "💬",
    image: "/slack.png",
    color: "bg-purple-600 hover:bg-purple-700 text-white",
    description: "Get channel info, user details, or search messages",
    systemPrompt:
      "You are a Slack integration assistant. Help users with Slack channel management, user queries, message searches, and workspace administration.",
  },
  {
    id: "jira",
    name: "Jira Assistant",
    icon: "🔷",
    image: "/jira.svg",
    color: "bg-blue-500 hover:bg-blue-600 text-white",
    description: "Check ticket status, create issues, or view reports",
    systemPrompt:
      "You are a Jira integration assistant. Help users with ticket management, issue creation, project tracking, and generating reports.",
  },
  {
    id: "github",
    name: "GitHub Assistant",
    icon: "🐙",
    image: "/github.png",
    color: "bg-purple-600 hover:bg-purple-700 text-white",
    description: "Review PRs, check issues, or get repo info",
    systemPrompt:
      "You are a GitHub integration assistant. Help users with pull request reviews, issue tracking, repository management, and code collaboration.",
  },
];

const quickActions = [
  "How to create new client?",
  "API documentation",
  "Troubleshoot reporting",
  "Mobile banking setup",
];

// Component
export default function ChatbotPage() {
  const auth = getAuth();
  const [currentUser, setCurrentUser] = useState(auth.currentUser);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user);
    });
    return () => unsubscribe(); // Cleanup the listener
  }, [auth]);

  // UI / mode
  const [selectedMode, setSelectedMode] = useState<string>("general");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // Chat history + conversations
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);

  // active conversation id per mode
  const [activeConversationIds, setActiveConversationIds] = useState<Record<string, string>>({});
  const [isCreatingNewChat, setIsCreatingNewChat] = useState<boolean>(false);

  // derived active conversation id for selected mode
  const activeConversationId = activeConversationIds[selectedMode];

  // General
  const [generalMessages, setGeneralMessages] = useState<MessageItem[]>([]);
  const [generalInput, setGeneralInput] = useState<string>("");
  const [generalStatus, setGeneralStatus] = useState<
    "ready" | "submitted" | "streaming" | "error"
  >("ready");
  const [generalError, setGeneralError] = useState<Error | undefined>(undefined);

  // Slack
  const [slackMessages, setSlackMessages] = useState<MessageItem[]>([]);
  const [slackInput, setSlackInput] = useState<string>("");
  const [slackStatus, setSlackStatus] = useState<
    "ready" | "submitted" | "streaming" | "error"
  >("ready");
  const [slackError, setSlackError] = useState<Error | undefined>(undefined);

  // Jira
  const [jiraMessages, setJiraMessages] = useState<MessageItem[]>([]);
  const [jiraInput, setJiraInput] = useState<string>("");
  const [jiraStatus, setJiraStatus] = useState<
    "ready" | "submitted" | "streaming" | "error"
  >("ready");
  const [jiraError, setJiraError] = useState<Error | undefined>(undefined);

  // GitHub
  const [githubMessages, setGithubMessages] = useState<MessageItem[]>([]);
  const [githubInput, setGithubInput] = useState<string>("");
  const [githubStatus, setGithubStatus] = useState<
    "ready" | "submitted" | "streaming" | "error"
  >("ready");
  const [githubError, setGithubError] = useState<Error | undefined>(undefined);

  // Helpers / Refs
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);
  const currentModeConfig = integrationModes.find((m) => m.id === selectedMode);

  // Load chats from Firestore (or create defaults)
  useEffect(() => {
    if (!currentUser) return;
    const fetchChats = async () => {
      try {
        const chatsCol = collection(db, "chats");
        const q = query(chatsCol, where("userId", "==", currentUser.uid));
        const chatsSnapshot = await getDocs(q);

        const chatsData: ChatHistoryItem[] = chatsSnapshot.docs.map((d) => {
          // Cast data shape to ChatHistoryItem fields except id (which comes from doc.id)
          const data = d.data() as Omit<ChatHistoryItem, "id">;
          return {
            id: d.id,
            title: data.title,
            date: data.date,
            icon: data.icon,
            messages: (data.messages ?? []) as MessageItem[],
            mode: data.mode,
            active: data.active ?? false,
            userId: data.userId
          };
        });

        if (chatsData.length === 0) {
          // Create default chats if none exist
          const defaultChatsDefaults = integrationModes.map((mode) => ({
            title: `New ${mode.name} Chat`,
            date: new Date().toLocaleDateString(),
            icon: mode.image,
            messages: [] as MessageItem[],
            mode: mode.id,
            active: false,
            userId: currentUser.uid,
          }));

          // Save them to Firestore and collect created docs with ids
          const created: ChatHistoryItem[] = [];
          for (const chatDef of defaultChatsDefaults) {
            const ref = await addDoc(collection(db, "chats"), chatDef);
            created.push({ ...chatDef, id: ref.id });
          }

          setChatHistory(created);
          setActiveConversationIds(
            created.reduce((acc, chat) => {
              acc[chat.mode] = chat.id;
              return acc;
            }, {} as Record<string, string>)
          );
        } else {
          setChatHistory(chatsData);
          setActiveConversationIds(
            chatsData.reduce((acc, chat) => {
              if (!acc[chat.mode]) acc[chat.mode] = chat.id;
              return acc;
            }, {} as Record<string, string>)
          );
        }
      } catch (err) {
        console.error("Failed loading chats from Firestore:", err);
      }
    };

    fetchChats();
    // We intentionally run this only on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser]);

  const generateChatTitle = (firstMessage: string) => {
    if (!firstMessage) return "New Chat";
    const words = firstMessage.split(" ").slice(0, 6).join(" ");
    return words.length > 40 ? words.substring(0, 40) + "..." : words;
  };

  // Update local state and Firestore (if conversation exists in DB)
  const updateLocalChatHistory = async (
    conversationId: string,
    updatedMessages: MessageItem[]
  ) => {
    setChatHistory((prev) =>
      prev.map((chat) =>
        chat.id === conversationId
          ? {
            ...chat,
            messages: updatedMessages,
            title:
              updatedMessages.length > 0
                ? generateChatTitle(updatedMessages[0].content)
                : chat.title,
          }
          : chat
      )
    );

    if (!conversationId) return;

    try {
      const chatRef = firestoreDoc(db, "chats", conversationId);
      await updateDoc(chatRef, {
        messages: updatedMessages,
        title:
          updatedMessages.length > 0
            ? generateChatTitle(updatedMessages[0].content)
            : "New Chat",
      });
    } catch (err) {
      // Firestore update might fail if doc doesn't exist yet — that's acceptable
      // We log it for debugging and continue with local state.
      console.warn("Failed to update chat in Firestore (it may not exist yet):", err);
    }
  };

  // create new conversation and return new id
  const createNewConversation = async (): Promise<string> => {
    setIsCreatingNewChat(true);
    const currentMode = integrationModes.find((m) => m.id === selectedMode);

    const newChatData: Omit<ChatHistoryItem, "id"> = {
      title: `New ${currentMode?.name || "Chat"}`,
      date: new Date().toLocaleDateString(),
      icon: currentMode?.image || "/mifos.png",
      messages: [],
      mode: selectedMode as any,
      active: true,
      userId: currentUser?.uid!
    };

    try {
      const docRef = await addDoc(collection(db, "chats"), newChatData);
      const newId = docRef.id;

      setChatHistory((prev) => [
        { ...newChatData, id: newId },
        ...prev.map((chat) => (chat.mode === selectedMode ? { ...chat, active: false } : chat)),
      ]);

      setActiveConversationIds((prev) => ({
        ...prev,
        [selectedMode]: newId,
      }));

      return newId;
    } catch (err) {
      console.error("Failed to create new conversation in Firestore:", err);
      // fallback: produce a local id so UI continues working
      const fallbackId = crypto.randomUUID();
      setChatHistory((prev) => [
        { ...newChatData, id: fallbackId },
        ...prev.map((chat) => (chat.mode === selectedMode ? { ...chat, active: false } : chat)),
      ]);
      setActiveConversationIds((prev) => ({
        ...prev,
        [selectedMode]: fallbackId,
      }));
      return fallbackId;
    } finally {
      setIsCreatingNewChat(false);
      setSidebarOpen(false);
    }
  };

  const sendMessage = async (
    mode: string,
    message: string,
    setInput: React.Dispatch<React.SetStateAction<string>>,
    setMessages: React.Dispatch<React.SetStateAction<MessageItem[]>>,
    setStatus: React.Dispatch<React.SetStateAction<"ready" | "submitted" | "streaming" | "error">>,
    setError: React.Dispatch<React.SetStateAction<Error | undefined>>,
    conversationId?: string
  ) => {
    if (!message.trim()) return;

    // ensure conversation exists
    let convId = conversationId ?? activeConversationIds[mode];
    if (!convId) {
      convId = await createNewConversation();
    }

    const userMessage: MessageItem = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
      timestamp: Date.now(),
    };

    // add user message locally and (attempt to) persist
    setMessages((prev) => {
      const updatedMessages = [...prev, userMessage];
      void updateLocalChatHistory(convId as string, updatedMessages);
      return updatedMessages;
    });
    setInput("");
    setStatus("submitted");

    try {
      // send to backend
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [userMessage],
          mode,
          conversationId: convId,
          userId: currentUser?.uid,
        }),
      });

      // stream response decoding (if your API streams)
      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantResponse = "";
      const assistantMessageId = crypto.randomUUID();

      // insert placeholder assistant message
      setMessages((prev) => {
        const updatedMessages = [
          ...prev,
          { id: assistantMessageId, role: "assistant" as "assistant", content: "", timestamp: Date.now() },
        ];
        void updateLocalChatHistory(convId as string, updatedMessages);
        return updatedMessages;
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        assistantResponse += decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const updatedMessages = prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, content: assistantResponse } : msg
          );
          void updateLocalChatHistory(convId as string, updatedMessages);
          return updatedMessages;
        });
      }

      setStatus("ready");
    } catch (err) {
      console.error(`Error sending ${mode} message:`, err);
      setError(err instanceof Error ? err : new Error(String(err)));
      setStatus("error");
    }
  };

  const handleGeneralSubmit = async (event?: { preventDefault?: () => void }) => {
    if (event?.preventDefault) event.preventDefault();
    await sendMessage(
      "general",
      generalInput,
      setGeneralInput,
      setGeneralMessages,
      setGeneralStatus,
      setGeneralError,
      activeConversationIds.general
    );
  };

  const handleSlackSubmit = async (event?: { preventDefault?: () => void }) => {
    if (event?.preventDefault) event.preventDefault();
    await sendMessage(
      "slack",
      slackInput,
      setSlackInput,
      setSlackMessages,
      setSlackStatus,
      setSlackError,
      activeConversationIds.slack
    );
  };

  const handleJiraSubmit = async (event?: { preventDefault?: () => void }) => {
    if (event?.preventDefault) event.preventDefault();
    await sendMessage(
      "jira",
      jiraInput,
      setJiraInput,
      setJiraMessages,
      setJiraStatus,
      setJiraError,
      activeConversationIds.jira
    );
  };

  const handleGithubSubmit = async (event?: { preventDefault?: () => void }) => {
    if (event?.preventDefault) event.preventDefault();
    await sendMessage(
      "github",
      githubInput,
      setGithubInput,
      setGithubMessages,
      setGithubStatus,
      setGithubError,
      activeConversationIds.github
    );
  };

  // This useEffect updates the messages state when the active conversation changes
  useEffect(() => {
    const currentChat = chatHistory.find((c) => c.id === activeConversationId);
    if (!currentChat) return;

    switch (selectedMode) {
      case "general":
        setGeneralMessages(currentChat.messages || []);
        break;
      case "slack":
        setSlackMessages(currentChat.messages || []);
        break;
      case "jira":
        setJiraMessages(currentChat.messages || []);
        break;
      case "github":
        setGithubMessages(currentChat.messages || []);
        break;
      default:
        break;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMode, activeConversationId, chatHistory]);

  const switchConversation = (conversationId: string) => {
    const conversation = chatHistory.find((c) => c.id === conversationId);
    if (!conversation) return;

    setActiveConversationIds((prev) => ({
      ...prev,
      [conversation.mode]: conversationId,
    }));

    switch (conversation.mode) {
      case "general":
        setGeneralMessages(conversation.messages || []);
        break;
      case "slack":
        setSlackMessages(conversation.messages || []);
        break;
      case "jira":
        setJiraMessages(conversation.messages || []);
        break;
      case "github":
        setGithubMessages(conversation.messages || []);
        break;
    }

    setSelectedMode(conversation.mode);
    setChatHistory((prev) => prev.map((chat) => ({ ...chat, active: chat.id === conversationId })));
    setSidebarOpen(false);
  };

  const deleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    const conversationToDelete = chatHistory.find((c) => c.id === conversationId);
    if (!conversationToDelete) return;

    const conversationsForMode = chatHistory.filter((c) => c.mode === conversationToDelete.mode);
    if (conversationsForMode.length <= 1) {
      return; // don't delete last conversation for a mode
    }

    try {
      await deleteDoc(firestoreDoc(db, "chats", conversationId));
    } catch (err) {
      console.warn("Failed to delete conversation from Firestore (maybe it's local-only):", err);
    }

    setChatHistory((prev) => prev.filter((c) => c.id !== conversationId));

    if (activeConversationIds[conversationToDelete.mode] === conversationId) {
      const remaining = chatHistory.filter((c) => c.id !== conversationId && c.mode === conversationToDelete.mode);
      if (remaining.length > 0) {
        const newActiveId = remaining[0].id;
        setActiveConversationIds((prev) => ({ ...prev, [conversationToDelete.mode]: newActiveId }));
        if (selectedMode === conversationToDelete.mode) {
          switchConversation(newActiveId);
        }
      }
    }
  };

  const handleModeChange = (modeId: string) => {
    setSelectedMode(modeId);

    const activeConvId = activeConversationIds[modeId];
    const activeConversation = chatHistory.find((c) => c.id === activeConvId);

    if (activeConversation) {
      setChatHistory((prev) => prev.map((chat) => ({ ...chat, active: chat.id === activeConvId })));

      switch (modeId) {
        case "general":
          setGeneralMessages(activeConversation.messages || []);
          break;
        case "slack":
          setSlackMessages(activeConversation.messages || []);
          break;
        case "jira":
          setJiraMessages(activeConversation.messages || []);
          break;
        case "github":
          setGithubMessages(activeConversation.messages || []);
          break;
      }
    }
  };

  const handleQuickAction = (action: string) => {
    switch (selectedMode) {
      case "general":
        setGeneralInput(action);
        break;
      case "slack":
        setSlackInput(action);
        break;
      case "jira":
        setJiraInput(action);
        break;
      case "github":
        setGithubInput(action);
        break;
    }

    setTimeout(() => {
      const form = document.querySelector("form");
      if (form) {
        form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      }
    }, 100);
  };

  const getCurrentAssistantState = () => {
    switch (selectedMode) {
      case "general":
        return {
          messages: generalMessages,
          input: generalInput,
          handleInputChange: (e: any) => setGeneralInput(e.target.value),
          handleSubmit: handleGeneralSubmit,
          status: generalStatus,
          stop: () => { },
          error: generalError,
          reload: () => {
            setGeneralError(undefined);
            setGeneralStatus("ready");
          },
          setMessages: setGeneralMessages,
        };
      case "slack":
        return {
          messages: slackMessages,
          input: slackInput,
          handleInputChange: (e: any) => setSlackInput(e.target.value),
          handleSubmit: handleSlackSubmit,
          status: slackStatus,
          stop: () => { },
          error: slackError,
          reload: () => {
            setSlackError(undefined);
            setSlackStatus("ready");
          },
          setMessages: setSlackMessages,
        };
      case "jira":
        return {
          messages: jiraMessages,
          input: jiraInput,
          handleInputChange: (e: any) => setJiraInput(e.target.value),
          handleSubmit: handleJiraSubmit,
          status: jiraStatus,
          stop: () => { },
          error: jiraError,
          reload: () => {
            setJiraError(undefined);
            setJiraStatus("ready");
          },
          setMessages: setJiraMessages,
        };
      case "github":
        return {
          messages: githubMessages,
          input: githubInput,
          handleInputChange: (e: any) => setGithubInput(e.target.value),
          handleSubmit: handleGithubSubmit,
          status: githubStatus,
          stop: () => { },
          error: githubError,
          reload: () => {
            setGithubError(undefined);
            setGithubStatus("ready");
          },
          setMessages: setGithubMessages,
        };
      default:
        return {
          messages: generalMessages,
          input: generalInput,
          handleInputChange: (e: any) => setGeneralInput(e.target.value),
          handleSubmit: handleGeneralSubmit,
          status: generalStatus,
          stop: () => { },
          error: generalError,
          reload: () => {
            setGeneralError(undefined);
            setGeneralStatus("ready");
          },
          setMessages: setGeneralMessages,
        };
    }
  };

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    status,
    stop,
    error,
    reload,
    setMessages,
  } = getCurrentAssistantState();

  const currentMode = integrationModes.find((m) => m.id === selectedMode);

  useEffect(() => {
    if (chatHistory.length > 0 && !activeConversationId) {
      const defaultChat = chatHistory.find((chat) => chat.mode === selectedMode);
      if (defaultChat) {
        setActiveConversationIds((prev) => ({
          ...prev,
          [selectedMode]: defaultChat.id,
        }));
      }
    }
  }, [chatHistory, activeConversationId, selectedMode]);

  return (
    <div className="flex bg-gray-50 dark:bg-gray-900 h-screen">
      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        chatHistory={chatHistory.filter((c) => c.mode === selectedMode)}
        isCreatingNewChat={isCreatingNewChat}
        createNewConversation={createNewConversation}
        switchConversation={switchConversation}
        deleteConversation={deleteConversation}
        integrationModes={integrationModes}
        currentMode={selectedMode}
      />

      <div className="flex flex-col flex-1 min-h-0">
        <ChatHeader
          currentMode={currentMode}
          isCreatingNewChat={isCreatingNewChat}
          setSidebarOpen={setSidebarOpen}
          createNewConversation={createNewConversation}
        />

        <ModeSelector
          integrationModes={integrationModes}
          selectedMode={selectedMode}
          handleModeChange={handleModeChange}
        />

        <ChatPanel
          key={`${selectedMode}-${activeConversationId}`}
          messages={messages}
          status={status}
          error={error}
          reload={reload}
          scrollAreaRef={scrollAreaRef}
          currentMode={currentMode}
          quickActions={quickActions}
          handleQuickAction={handleQuickAction}
          integrationModes={integrationModes}
        />

        <MessageInput
          input={input}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          status={status}
          stop={stop}
          currentModeName={currentMode?.name}
        />
      </div>
    </div>
  );
}
