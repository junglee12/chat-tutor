import streamlit as st
import os
import google.generativeai as genai
from pypdf import PdfReader
import io
from dotenv import load_dotenv
import csv

# Constants
CHAT_OPTIONS = {
    "converse": "Converse with Gemini 2.0",
    "files": "Chat with Files",
}

FORMATTING_INSTRUCTIONS = (
    "System instruction: You are a friendly and patient guide for kids! Explain concepts in a simple, fun, and engaging way, using examples that kids can understand (like toys, animals, or games)."
    "Guide the kids through the problem step-by-step, but NEVER give the final answer at all cost. Instead, stop at mid-steps and encourage the children to get to calculate the final answer by children."
    "You will NEVER solve or try to solve the problem. Only kids gets to solve or try do solve."
    "For example, if the last step is '90 ÷ 0.5', say something like 'Now you try! What is 90 ÷ 0.5? I'll be here until you finish!'"
)

MODEL_ID = 'gemini-2.0-flash'
TEMPERATURE = 0.6

# Page Setup


def setup_page():
    st.set_page_config(page_title="⚡ Chatbot", layout="centered")
    st.header("Chatbot")
    st.sidebar.header("Options", divider='rainbow')
    st.markdown(
        "<style>#MainMenu {visibility: hidden;}</style>", unsafe_allow_html=True)

    # Inject MathJax to render LaTeX
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

# File Processing


def process_file(uploaded_file, model):
    file_type, file_name = uploaded_file.type, uploaded_file.name
    content_parts, token_count = [], 0

    if file_type == "application/pdf":
        try:
            pdf_reader = PdfReader(uploaded_file)
            text = "".join(page.extract_text()
                           or "" for page in pdf_reader.pages)
            content = f"PDF '{file_name}' content: {text}" if text else f"PDF '{file_name}': No text extracted."
            content_parts.append(content)
            token_count = model.count_tokens(content).total_tokens
        except Exception as e:
            content_parts.append(
                f"PDF '{file_name}': Error processing - {str(e)}")

    elif file_type in ["image/jpeg", "image/png"]:
        try:
            image_bytes = uploaded_file.read()
            content = {"mime_type": file_type, "data": image_bytes}
            content_parts.append(content)
            token_count = model.count_tokens("Image placeholder").total_tokens
        except Exception as e:
            content_parts.append(
                f"Image '{file_name}': Error processing - {str(e)}")

    elif file_type == "text/plain":
        try:
            text = uploaded_file.read().decode("utf-8")
            content = f"Text file '{file_name}' content: {text}" if text else f"Text file '{file_name}': Empty file."
            content_parts.append(content)
            token_count = model.count_tokens(content).total_tokens
        except Exception as e:
            content_parts.append(
                f"Text file '{file_name}': Error processing - {str(e)}")

    elif file_type == "text/csv":
        try:
            csv_content = uploaded_file.read().decode("utf-8")
            csv_reader = csv.reader(io.StringIO(csv_content))
            csv_text = "\n".join([", ".join(row) for row in csv_reader])
            content = f"CSV file '{file_name}' content:\n{csv_text}" if csv_text else f"CSV file '{file_name}': Empty file."
            content_parts.append(content)
            token_count = model.count_tokens(content).total_tokens
        except Exception as e:
            content_parts.append(
                f"CSV file '{file_name}': Error processing - {str(e)}")

    else:
        content = f"File '{file_name}' ({file_type}): Processing not supported yet."
        content_parts.append(content)
        token_count = model.count_tokens(content).total_tokens

    return content_parts, token_count

# Session Management


def init_session():
    defaults = {
        "message": "",
        "chat_history": [],
        "uploaded_file_contents": [],
        "total_tokens": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_session():
    for key in ["chat", "message", "chat_history", "total_tokens", "uploaded_file_contents"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.total_tokens = 0

# Chat Handling


def init_chat(model, mode):
    welcome_msg = "Understood! How can I assist you?" if mode == CHAT_OPTIONS[
        "converse"] else "Understood! How can I assist you with your files?"
    initial_history = [
        {"role": "user", "parts": [FORMATTING_INSTRUCTIONS]},
        {"role": "model", "parts": [welcome_msg]}
    ]
    st.session_state.chat = model.start_chat(history=initial_history)
    for msg in initial_history:
        for part in msg["parts"]:
            st.session_state.total_tokens += model.count_tokens(
                part).total_tokens


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
            response = st.session_state.chat.send_message(
                [prompt] + st.session_state.uploaded_file_contents)
        else:
            response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text, unsafe_allow_html=True)
        response_tokens = model.count_tokens(response.text).total_tokens
        st.session_state.total_tokens += response_tokens
        st.session_state.chat_history.append(
            {"role": "model", "content": response.text})
    st.session_state.message += response.text

# Main Logic


def main():
    # Setup environment and model
    load_dotenv()
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        st.stop()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_ID, generation_config={
                                  "temperature": TEMPERATURE})

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
    if choice == CHAT_OPTIONS["files"]:
        st.subheader("Chat with your files")
        if 'chat' not in st.session_state:
            init_chat(model, choice)
        render_chat_history()
        if prompt := st.chat_input("Ask a question about your files"):
            with st.chat_message("user"):
                st.write(prompt)
            handle_chat_input(model, prompt, use_file_contents=True)

    def clear_session():
        for key in ["chat", "message", "chat_history", "total_tokens", "uploaded_file_contents", "processed_file_names"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.total_tokens = 0

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
