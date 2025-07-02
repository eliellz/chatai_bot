# AI Chatbot Portal using Streamlit and LangChain
# This script creates a web application where users can upload a text document
# and ask questions about its content. The chatbot uses OpenAI's language models
# to understand the document and provide answers.

# --- Installation ---
# To run this app, you need to install the following libraries.
# You can create a 'requirements.txt' file and paste the following lines into it:
#
# streamlit
# langchain
# openai
# faiss-cpu
# tiktoken
#
# Then, run this command in your terminal:
# pip install -r requirements.txt
#
# --- How to Run ---
# 1. Save this code as a Python file (e.g., `app.py`).
# 2. Make sure you have your OpenAI API key.
# 3. Open your terminal or command prompt.
# 4. Navigate to the directory where you saved `app.py`.
# 5. Run the app with the command: streamlit run app.py

import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.base import BaseCallbackHandler

# Custom handler to display the thinking process in the UI
class StreamlitCallbackHandler(BaseCallbackHandler):
    """A custom callback handler that writes intermediate steps to the Streamlit UI."""
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Append new tokens to the text and update the container."""
        self.text += token
        self.container.markdown(self.text)

def process_document(document_text, openai_api_key):
    """
    Processes the uploaded document text by splitting it into chunks,
    creating embeddings, and storing them in a vector store.

    Args:
        document_text (str): The text content of the uploaded document.
        openai_api_key (str): The user's OpenAI API key.

    Returns:
        FAISS: A vector store containing the document's text chunks.
    """
    try:
        # 1. Split the document into smaller chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(document_text)

        if not chunks:
            st.error("Could not split the document into chunks. Please check the document format.")
            return None

        # 2. Create embeddings for the chunks using OpenAI
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        # 3. Create a FAISS vector store from the embeddings
        # This allows for efficient similarity searches
        vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
        return vectorstore

    except Exception as e:
        st.error(f"An error occurred during document processing: {e}")
        return None

def get_conversation_chain(vectorstore, openai_api_key):
    """
    Creates a conversational retrieval chain.

    Args:
        vectorstore (FAISS): The vector store containing the document embeddings.
        openai_api_key (str): The user's OpenAI API key.

    Returns:
        ConversationalRetrievalChain: The initialized conversation chain.
    """
    # Initialize the language model
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_key=openai_api_key,
        streaming=True # Enable streaming for a more interactive experience
    )

    # Set up memory to keep track of the conversation history
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True
    )

    # Create the conversation chain
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def main():
    """The main function that runs the Streamlit application."""
    # --- Page Configuration ---
    st.set_page_config(page_title="AI Document Portal", page_icon="🤖")

    # --- Session State Initialization ---
    # Initialize session state variables if they don't exist
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "document_processed" not in st.session_state:
        st.session_state.document_processed = False

    # --- Sidebar for API Key and Document Upload ---
    with st.sidebar:
        st.header("Configuration")
        st.markdown(
            "Welcome to the AI Document Portal! "
            "Upload a document, and the AI will answer your questions about it."
        )

        # Get OpenAI API Key from the user
        openai_api_key = st.text_input(
            "Enter your OpenAI API Key:",
            type="password",
            help="You can get your API key from https://platform.openai.com/account/api-keys"
        )

        st.subheader("Upload Your Document")
        # File uploader for text-based documents
        uploaded_file = st.file_uploader(
            "Choose a .txt file",
            type=['txt']
        )

        # Process the document when the button is clicked
        if st.button("Process Document"):
            if uploaded_file is not None and openai_api_key:
                with st.spinner("Processing document... This may take a moment."):
                    # Read the content of the uploaded file
                    document_text = uploaded_file.getvalue().decode("utf-8")

                    # Process the document to create a vector store
                    vectorstore = process_document(document_text, openai_api_key)

                    if vectorstore:
                        # Create the conversation chain
                        st.session_state.conversation = get_conversation_chain(vectorstore, openai_api_key)
                        st.session_state.document_processed = True
                        st.success("Document processed successfully! You can now ask questions.")
                    else:
                        st.error("Failed to process the document.")
            elif not openai_api_key:
                st.warning("Please enter your OpenAI API key to proceed.")
            else:
                st.warning("Please upload a document to process.")

    # --- Main Chat Interface ---
    st.title("🤖 AI Document Portal")
    st.markdown("Ask a question about the content of your uploaded document.")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if user_question := st.chat_input("Your question:", disabled=not st.session_state.document_processed):
        # Add user question to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        # Get the AI's response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            # Use the custom callback handler to stream the response
            callback_handler = StreamlitCallbackHandler(container=message_placeholder)
            
            try:
                response = st.session_state.conversation({
                    'question': user_question
                }, callbacks=[callback_handler])
                
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response['chat_history'][-1].content})

            except Exception as e:
                st.error(f"An error occurred while generating the response: {e}")


if __name__ == '__main__':
    main()
