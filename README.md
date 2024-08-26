# Mifos Web-App Chatbot

## Project Overview

The Mifos Web-App Chatbot is a cutting-edge project exploring the use of generative AI to enhance community support mechanisms for implementers and adopters of Mifos and Fineract. As the Mifos community has grown, so has the complexity of its applications. This chatbot aims to provide swift, accurate support to users, especially those new to the projects.

### Background

- The Mifos community has expanded significantly in recent years.
- Mifos applications are highly complex, requiring specialized support for implementation and development.
- Current support is primarily through Slack general channels and dispersed documentation.
- Response times and quality can vary based on who reads and responds to queries.
- There is no dedicated resource for consistent monitoring and response, leading to potential delays.

### Project Objectives

1. Develop an AI-powered chatbot capable of understanding and responding to user queries about Mifos and Fineract products.
2. Create a learning algorithm that improves the bot's responses over time.
3. Provide users with relevant answers or direct them to appropriate documentation.
4. Cover the range of Mifos/Fineract products currently supported in the Slack channel.
5. Implement pre-training of algorithms based on historical questions and responses.
6. Streamline the support process for implementers and adopters of Mifos and Fineract.

## Features

- Natural language processing to understand user queries
- Integration with OpenAI's GPT models for generating responses
- Vector embeddings for efficient information retrieval from the codebase
- Support for multiple file types including TypeScript, HTML, Markdown, and JavaScript
- User-friendly interface built with Gradio

## Technology Stack

- Python 3.8+
- LangChain for NLP tasks
- OpenAI GPT models
- ChromaDB for vector storage
- Gradio for the user interface

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/openMF/community-ai.git
   cd mifos-web-app-chatbot
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   Create a `.env` file in the root directory and add:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

To run the chatbot locally, the ipynb file can be used. The Gradio interface will start, allowing you to interact with the chatbot. 

1. Run the following command:
   ```
   jupyter notebook
   ```
2. Open the `web-app_bot.ipynb` file in the Jupyter Notebook interface.
3. Run the cells to start the chatbot.
4. Enter your query in the text box and click the "Submit" button to get a response.
5. The chatbot will display the most relevant code snippets or documentation based on your query.

OR

To use the deployed version of the chatbot, visit the following link: [Mifos Web-App Chatbot](https://huggingface.co/spaces/MifosBot/Web-App)

## Project Structure

- `CodeCommentingScript.py`: Main script containing the logic for data pre-processing as explained in ![Report] (https://gist.github.com/shubhampal62/f7e5331dc58af05f19e959f847c9d3e5)
- `web-app/`: Directory containing the Mifos Web-App files for analysis
- `web_app_vector_storage_metadata/`: Directory for storing vector embeddings
- `requirements.txt`: List of Python dependencies

## How It Works

1. The chatbot processes and indexes the Mifos Web-App codebase, creating vector embeddings for efficient retrieval.
2. When a user asks a question, the system finds the most relevant code snippets or documentation.
3. The chatbot then uses GPT models to generate a human-like response based on the retrieved information.
4. Responses focus on file organization, key components, and project structure.

## Contributing

We welcome contributions to improve the Mifos Web-App Chatbot. Please feel free to submit issues, feature requests, or pull requests.

---

For more information about Mifos and Fineract, visit [https://mifos.org/](https://mifos.org/)