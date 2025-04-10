# AI-Powered Educational Chatbot

A Streamlit-based application that uses Google's Gemini AI to provide interactive tutoring and file analysis capabilities.

## Description

An AI-powered educational chatbot that helps students learn through interactive conversations and document analysis. Key features include:

- Child-friendly explanations with step-by-step guidance
- Multi-file format support (PDF, images, text, CSV)
- Customizable AI model parameters
- Real-time token usage tracking

## Features

- Interactive chat interface with two modes: general conversation and document analysis
- File upload and processing capabilities
- Session management and history
- Math expression rendering using LaTeX

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-chatbot.git
cd ai-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Google API key:
```bash
echo 'GOOGLE_API_KEY=your_api_key_here' > .env
```

## Usage

Start the Streamlit application with:
```bash
streamlit run app.py
```

The application will open in your default web browser. Use the sidebar to:
1. Choose between conversation modes
2. Upload files for analysis (PDF, images, text, CSV)
3. Adjust model settings (temperature, max tokens)
4. Start new sessions

## Requirements

- Python 3.8+
- Google API key (free tier available)
- Packages:
  - Streamlit (web interface)
  - Google Generative AI (AI capabilities)
  - pypdf (PDF processing)
  - python-dotenv (environment variables)

## Project Structure
```
.
├── README.md
├── app.py
├── requirements.txt
└── .env (after configuration)
