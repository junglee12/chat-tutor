import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Constants
CHAT_OPTIONS = {"converse": "Converse with Gemini 2.0",
                "files": "Chat with Files"}
DEFAULT_MODEL = 'gemini-2.0-flash'
DEFAULT_TEMPERATURE = 0.55
MODEL_OPTIONS = ['gemini-2.0-flash', 'gemini-2.0-flash',]
FORMATTING_INSTRUCTIONS = (
    "System instruction: You are a friendly and patient guide for kids! Explain concepts in a simple, fun, "
    "and engaging way, using examples that kids can understand (like toys, animals, or games). Guide the kids "
    "through the problem step-by-step, but NEVER give the final answer. Stop at mid-steps and encourage them to "
    "You will NEVER solve or try to solve the problem. Only kids gets to solve or try do solve."
    "calculate the final answer themselves. For example, if the last step is '90 ÷ 0.5', say 'Now you try! What "
    "is 90 ÷ 0.5? I’ll be here until you finish!'"
)

# Setup Functions


def setup_page():
    st.set_page_config(page_title="⚡ Chatbot",
                       layout="centered", menu_items={})
    st.header("Chatbot")
    st.sidebar.header("Options", divider='rainbow')
    st.components.v1.html(
        """<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
        <script type="text/x-mathjax-config">MathJax.Hub.Config({tex2jax: {inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']], processEscapes: true}});</script>""",
        height=0  # Invisible component
    )


def configure_model():
    load_dotenv()
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai

# Sidebar Controls


def get_sidebar_controls():
    # Default to "Chat with Files"
    choice = st.sidebar.radio("Choose:", list(CHAT_OPTIONS.values()), index=1)
    clear = st.sidebar.button("Start new session", key="clear")
    uploaded_files = st.sidebar.file_uploader(
        "Upload files to chat about", accept_multiple_files=True, key="file_uploader") if choice == CHAT_OPTIONS["files"] else None
    model_name, temperature, max_tokens = get_settings()
    return choice, clear, uploaded_files, model_name, temperature, max_tokens


def get_settings():
    with st.sidebar.expander("Settings", expanded=False):
        model_name = st.selectbox(
            "Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(DEFAULT_MODEL))
        temperature = st.slider("Temperature", 0.0, 1.0,
                                DEFAULT_TEMPERATURE, step=0.01)
        max_tokens = st.number_input(
            "Max Output Tokens", 50, 8192, 8192, step=50)
    return model_name, temperature, max_tokens

# Session Management


def init_session():
    defaults = {"message": "", "chat_history": [], "uploaded_file_contents": [
    ], "total_tokens": 0, "processed_file_names": set()}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def clear_session():
    keys = ["chat", "message", "chat_history", "total_tokens",
            "uploaded_file_contents", "processed_file_names", "model"]
    for key in keys:
        st.session_state.pop(key, None)
    st.session_state.total_tokens = 0

# File Processing


def process_file(uploaded_file, model):
    file_type, file_name = uploaded_file.type, uploaded_file.name
    content_parts, token_count = [], 0
    try:
        file_bytes = uploaded_file.read()
        content = {"mime_type": file_type, "data": file_bytes, "name": file_name}
        content_parts.append(content)
        token_count = model.count_tokens(f"Placeholder for {file_name}").total_tokens
    except Exception as e:
        error_msg = f"Error loading '{file_name}' ({file_type}): {str(e)}"
        st.sidebar.write(error_msg)
        content_parts.append(error_msg)
        token_count = model.count_tokens(error_msg).total_tokens
    return content_parts, token_count


def process_uploaded_files(uploaded_files, model):
    if not uploaded_files:
        return
    new_parts = []
    for file in uploaded_files:
        if file.name not in st.session_state.processed_file_names:
            parts, tokens = process_file(file, model)
            new_parts.extend(parts)
            st.session_state.total_tokens += tokens
            st.session_state.processed_file_names.add(file.name)
    if new_parts:
        st.session_state.uploaded_file_contents.extend(new_parts)
        # Strip 'name' field before appending to chat history
        history_parts = [{"mime_type": part["mime_type"], "data": part["data"]} for part in new_parts]
        st.session_state.chat.history.append({"role": "user", "parts": history_parts})

# Chat Handling


def init_chat(model, mode):
    welcome_msg = "Understood! How can I assist you?" if mode == CHAT_OPTIONS[
        "converse"] else "Understood! How can I assist you with your files?"
    initial_history = [{"role": "user", "parts": [FORMATTING_INSTRUCTIONS]}, {
        "role": "model", "parts": [welcome_msg]}]
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
    st.session_state.total_tokens += model.count_tokens(prompt).total_tokens
    with st.chat_message("model", avatar="🧞‍♀️"):
        if use_file_contents and st.session_state.uploaded_file_contents:
            model_content = [prompt] + [{"mime_type": item["mime_type"], "data": item["data"]} for item in st.session_state.uploaded_file_contents]
        else:
            model_content = prompt
        response = st.session_state.chat.send_message(model_content)
        st.markdown(response.text, unsafe_allow_html=True)
        st.session_state.total_tokens += model.count_tokens(response.text).total_tokens
        st.session_state.chat_history.append({"role": "model", "content": response.text})
    st.session_state.message += response.text

# Main Logic


def update_model(genai, model_name, temperature, max_tokens):
    settings_changed = (
        "model_settings" not in st.session_state or
        model_name != st.session_state.model_settings["model_name"] or
        temperature != st.session_state.model_settings["temperature"] or
        max_tokens != st.session_state.model_settings["max_tokens"]
    )
    if "model" not in st.session_state or settings_changed:
        st.session_state.model = genai.GenerativeModel(model_name, generation_config={
                                                       "temperature": temperature, "max_output_tokens": max_tokens})
        st.session_state.model_settings = {
            "model_name": model_name, "temperature": temperature, "max_tokens": max_tokens}
        if "chat" in st.session_state:
            del st.session_state.chat
    return st.session_state.model


def main():
    setup_page()
    genai = configure_model()
    choice, clear, uploaded_files, model_name, temperature, max_tokens = get_sidebar_controls()
    model = update_model(genai, model_name, temperature, max_tokens)

    if clear:
        clear_session()
    init_session()

    if 'chat' not in st.session_state:
        init_chat(model, choice)

    process_uploaded_files(uploaded_files, model)

    # Separate expanders for Uploaded Files and Processed File Names
    with st.sidebar.expander("Uploaded Files", expanded=False):
        if uploaded_files is not None and uploaded_files:
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. {file.name}")
        else:
            st.write("None")

    with st.sidebar.expander("Processed File Names", expanded=False):
        if st.session_state.processed_file_names:
            for i, file_name in enumerate(st.session_state.processed_file_names, 1):
                st.write(f"{i}. {file_name}")
        else:
            st.write("None")

    # File Contents Expander (unchanged)
    with st.sidebar.expander("File Contents", expanded=False):
        if st.session_state.uploaded_file_contents:
            for i, content in enumerate(st.session_state.uploaded_file_contents, 1):
                mime_type = content.get("mime_type", "Unknown")
                file_name = content.get("name", f"File {i}")
                size_in_bytes = len(content.get('data', b''))
                size_in_mb = size_in_bytes / (1024 * 1024)  # Convert bytes to MB
                st.write(f"{i}. {file_name}: Type={mime_type}, Size={size_in_mb:.2f} MB")
        else:
            st.write("No files loaded.")

    if choice == CHAT_OPTIONS["converse"]:
        st.subheader("Ask Gemini")
        render_chat_history()
        if prompt := st.chat_input("Enter your question here"):
            with st.chat_message("user"):
                st.write(prompt)
            handle_chat_input(model, prompt)
    else:  # CHAT_OPTIONS["files"]
        st.subheader("Chat with your files")
        render_chat_history()
        if prompt := st.chat_input("Ask a question about your files"):
            with st.chat_message("user"):
                st.write(prompt)
            handle_chat_input(model, prompt, use_file_contents=True)

    st.sidebar.write(f"Total Tokens Used: {st.session_state.total_tokens}")


if __name__ == "__main__":
    main()
