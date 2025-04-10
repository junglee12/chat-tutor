import streamlit as st
import os
import google.generativeai as genai
from pypdf import PdfReader
import io
from dotenv import load_dotenv
import csv

# Constants
CHAT_OPTIONS = {
    "converse": "Converse with AI Tutor",
    "files": "Chat with Files",
}

FORMATTING_INSTRUCTIONS = (
    "System instruction: You are a friendly and patient guide for kids! Explain concepts in a simple, fun, and engaging way, using examples that kids can understand (like toys, animals, or games)."
    "Guide the kids through the problem step-by-step, but NEVER give the final answer at all cost. Instead, stop at mid-steps and encourage the children to get to calculate the final answer by children."
    "You will NEVER solve or try to solve the problem. Only kids gets to solve or try do solve."
    "For example, if the last step is '90 ÷ 0.5', say something like 'Now you try! What is 90 ÷ 0.5? I'll be here until you finish!'"
)

# Default settings
DEFAULT_MODEL = 'gemini-2.0-flash'
DEFAULT_TEMPERATURE = 0.55
MODEL_OPTIONS = ['gemini-2.0-flash','gemini-2.0-flash-lite']  # Example model names

# Page Setup
def setup_page():
    st.set_page_config(page_title="⚡ Chatbot", layout="centered")
    st.header("Chatbot")
    st.sidebar.header("Options", divider='rainbow')
    st.markdown("<style>#MainMenu {visibility: hidden;}</style>", unsafe_allow_html=True)

    # Inject MathJax for LaTeX rendering
    st.markdown("""
    <script type="text/javascript" async
      src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
    <script type="text/x-mathjax-config">
      MathJax.Hub.Config({
        tex2jax: {
          inlineMath: [['\\(', '\\)']],
          displayMath: [['\\[', '\\]']],
          processEscapes: true
        }
      });
    </script>
    """, unsafe_allow_html=True)

# Sidebar Controls
def get_choice():
    return st.sidebar.radio("Choose:", list(CHAT_OPTIONS.values()))

def get_clear():
    return st.sidebar.button("Start new session", key="clear")

def get_file_uploader(selected_choice):
    return st.sidebar.file_uploader("Upload files to chat about", accept_multiple_files=True, key="file_uploader") if selected_choice == CHAT_OPTIONS["files"] else None

def get_settings():
    with st.sidebar.expander("Settings", expanded=False):
        model_name = st.selectbox("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(DEFAULT_MODEL))
        temperature = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, step=0.1)
        max_tokens = st.number_input("Max Output Tokens", min_value=50, max_value=8192, value=1024, step=50)
    return model_name, temperature, max_tokens

# File Processing (unchanged)
def process_file(uploaded_file, model):
    # [Existing process_file code remains unchanged]
    file_type, file_name = uploaded_file.type, uploaded_file.name
    content_parts, token_count = [], 0
    # ... rest of the function ...
    return content_parts, token_count

# Session Management
def init_session():
    defaults = {
        "message": "",
        "chat_history": [],
        "uploaded_file_contents": [],
        "total_tokens": 0,
        "processed_file_names": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_session():
    for key in ["chat", "message", "chat_history", "total_tokens", "uploaded_file_contents", "processed_file_names"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.total_tokens = 0

# Chat Handling
def init_chat(model, mode):
    welcome_msg = "Understood! How can I assist you?" if mode == CHAT_OPTIONS["converse"] else "Understood! How can I assist you with your files?"
    initial_history = [
        {"role": "user", "parts": [FORMATTING_INSTRUCTIONS]},
        {"role": "model", "parts": [welcome_msg]}
    ]
    st.session_state.chat = model.start_chat(history=initial_history)
    for msg in initial_history:
        for part in msg["parts"]:
            st.session_state.total_tokens += model.count_tokens(part).total_tokens

def render_chat_history():
    with st.container():
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"], unsafe_allow_html=True)

def handle_chat_input(model, prompt, use_file_contents=False):
    st.session_state.message += prompt
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    prompt_tokens = model.count_tokens(prompt).total_tokens
    st.session_state.total_tokens += prompt_tokens

    with st.chat_message("model", avatar="🧞‍♀️"):
        if use_file_contents and st.session_state.uploaded_file_contents:
            response = st.session_state.chat.send_message([prompt] + st.session_state.uploaded_file_contents)
        else:
            response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text, unsafe_allow_html=True)
        response_tokens = model.count_tokens(response.text).total_tokens
        st.session_state.total_tokens += response_tokens
        st.session_state.chat_history.append({"role": "model", "content": response.text})
    st.session_state.message += response.text

# Main Logic
def main():
    # Setup environment
    load_dotenv()
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        st.stop()

    genai.configure(api_key=api_key)

    # Initialize session and settings
    if "model_settings" not in st.session_state:
        st.session_state.model_settings = {"model_name": DEFAULT_MODEL, "temperature": DEFAULT_TEMPERATURE, "max_tokens": 1024}

    # Get settings from sidebar
    model_name, temperature, max_tokens = get_settings()

    # Only recreate model if settings changed
    settings_changed = (
        model_name != st.session_state.model_settings["model_name"] or
        temperature != st.session_state.model_settings["temperature"] or
        max_tokens != st.session_state.model_settings["max_tokens"]
    )
    if "model" not in st.session_state or settings_changed:
        st.session_state.model = genai.GenerativeModel(
            model_name,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
        )
        st.session_state.model_settings = {"model_name": model_name, "temperature": temperature, "max_tokens": max_tokens}
        if "chat" in st.session_state:  # Reset chat only if model changes
            del st.session_state.chat

    model = st.session_state.model

    # Get user inputs
    choice = get_choice()
    clear = get_clear()
    uploaded_files = get_file_uploader(choice)

    # Handle session
    if clear:
        clear_session()
    init_session()

    # Track processed file names
    if "processed_file_names" not in st.session_state:
        st.session_state.processed_file_names = set()

    # Process only new uploaded files
    if uploaded_files:
        new_parts = []
        for file in uploaded_files:
            if file.name not in st.session_state.processed_file_names:
                parts, tokens = process_file(file, model)
                new_parts.extend(parts)
                st.session_state.total_tokens += tokens
                st.session_state.processed_file_names.add(file.name)  # Mark as processed
        if new_parts:
            st.session_state.uploaded_file_contents.extend(new_parts)
            st.session_state.chat.history.append({"role": "user", "parts": new_parts})

    # Handle chat modes
    if choice == CHAT_OPTIONS["converse"]:
        st.subheader("Ask Gemini")
        if 'chat' not in st.session_state:
            init_chat(model, choice)
        render_chat_history()
        if prompt := st.chat_input("Enter your question here"):
            with st.chat_message("user"):
                st.write(prompt)
            handle_chat_input(model, prompt)

    elif choice == CHAT_OPTIONS["files"]:
        st.subheader("Chat with your files")
        if 'chat' not in st.session_state:
            init_chat(model, choice)
        render_chat_history()
        if prompt := st.chat_input("Ask a question about your files"):
            with st.chat_message("user"):
                st.write(prompt)
            handle_chat_input(model, prompt, use_file_contents=True)

    # Display token count
    st.sidebar.write(f"Total Tokens Used: {st.session_state.total_tokens}")

if __name__ == '__main__':
    setup_page()
    main()