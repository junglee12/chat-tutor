# Gemini Chat Interface

A Streamlit-based chat interface for Google's Gemini AI with file upload capabilities.

![App Screenshot](screenshot.png)

## Features

- 💬 Chat with Gemini 2.0 Flash model
- 📁 Upload and chat about files (PDF, text, images)
- ⚙️ Adjustable model parameters (temperature, max tokens)
- 📊 Real-time token usage tracking
- 🔄 Session management with clear history

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

## Usage
```bash
streamlit run app.py
```

- Upload files via sidebar
- Choose chat mode (conversation or file-based)
- Adjust model settings in sidebar
- Type your prompt in the chat input

## Configuration
- Edit `.env` file to set API keys
- Modify `app.py` to change default model parameters
- Update `FORMATTING_INSTRUCTIONS` in code for different interaction styles

## Requirements
- Python 3.9+
- Google API key with Gemini access
