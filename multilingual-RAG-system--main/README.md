# RAG_PDF_chatbot
# 📄 Chat with PDFs — Multilingual RAG App using Groq API

This is a Streamlit-based web app that allows you to upload one or more PDFs and ask questions about their content. It uses **Groq LLMs** for answering queries based on document context with **HuggingFace embeddings** and **FAISS vector store**.

---

## 🚀 Features

- 📚 Upload and parse one or multiple PDF files.
- 🧠 Uses vector search (FAISS) for semantic retrieval.
- 💬 Groq LLM for accurate, grounded answers.
- 🔁 Maintains chat history for conversational context.
- 🌍 Multilingual support for both documents and questions.
- ⚡ Fast and interactive Streamlit UI.

---

## 🛠️ Requirements

- Python 3.8+
- A free or paid [Groq API Key](https://console.groq.com/)
- HuggingFace-compatible embedding model

---

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/pdf-chat-groq.git
   cd pdf-chat-groq
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set up .env file
Create a .env file in the root directory with the following:

env
Copy
Edit
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=llama3-8b-8192  # or another supported Groq model
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
🖥️ Usage
Run the Streamlit app:

bash
Copy
Edit
streamlit run 2632d3ee-1677-43e9-b70a-e73f05904326.py
Then go to http://localhost:8501 in your browser.

📁 Project Structure
bash
Copy
Edit
.
├── 2632d3ee-1677-43e9-b70a-e73f05904326.py  # Main Streamlit app
├── htmlTemplates/
│   ├── bot_template.html
│   └── user_template.html
├── .env
├── requirements.txt
└── README.md
✅ To-Do
 Add PDF summarization feature

 Integrate multilingual PDF OCR (Tesseract)

 Dockerize the app
 
 To see demo just click on 'view raw' 

🤝 Contributing
PRs are welcome! For major changes, please open an issue first.
