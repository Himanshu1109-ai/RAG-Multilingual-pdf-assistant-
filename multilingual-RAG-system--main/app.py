
import os
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import traceback
# dotenv: load .env located next to this script so Streamlit subprocess picks it up
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

# Read GROQ model default at import time, but read the API key at runtime
# to ensure the running Streamlit process sees the loaded environment.
groq_model_default = os.environ.get("GROQ_MODEL_NAME") or "llama-3.1-8b-instant"
# Use env var if provided; otherwise default to a widely-used small multilingual
# sentence-transformers model so embeddings work out-of-the-box.
embedding_model = os.environ.get("EMBEDDING_MODEL_NAME") or "sentence-transformers/all-MiniLM-L6-v2"


# For Windows users, you might need to set the tesseract command path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import streamlit as st
# PyPDF2 is no longer needed for extraction
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.memory.zep_cloud_memory import ConversationBufferMemory
from langchain_classic.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_groq import ChatGroq

from htmlTemplates import bot_template, user_template, css

# -------------------- PDF & Text Chunking (with OCR) --------------------
pytesseract.pytesseract.tesseract_cmd =r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Try to use a PDF text extractor first (avoids Poppler when PDFs contain selectable text)
PdfReader = None
try:
    import importlib
    _py = importlib.import_module('PyPDF2')
    PdfReader = getattr(_py, 'PdfReader', getattr(_py, 'PdfFileReader', None))
    if PdfReader is None:
        PdfReader = None
except Exception:
    try:
        import importlib
        _py = importlib.import_module('pypdf')
        PdfReader = getattr(_py, 'PdfReader', None)
        if PdfReader is None:
            PdfReader = None
    except Exception:
        PdfReader = None


def get_pdf_text_with_ocr(pdf_files, languages):
    """
    Extracts text from PDF files using OCR.
    Converts each PDF page to an image and uses Tesseract to extract text.
    """
    text = ""
    # Convert tesseract language codes (e.g., ['eng', 'fra']) to the format needed ('eng+fra')
    lang_str = '+'.join(languages)
    
    for pdf_file in pdf_files:
        # Read PDF from bytes
        pdf_bytes = pdf_file.read()

        # First try to extract text using a PDF text extractor (no Poppler needed)
        extracted_text = ""
        if PdfReader is not None:
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                pages_text = []
                for p in reader.pages:
                    try:
                        page_text = p.extract_text() or ""
                    except Exception:
                        page_text = ""
                    pages_text.append(page_text)
                extracted_text = "\n".join(pages_text).strip()
            except Exception:
                extracted_text = ""

        # If we found reasonable extracted text, use it and skip OCR
        if extracted_text and len(extracted_text) > 20:
            text += extracted_text + "\n"
            continue

        # Fallback to OCR via pdf2image + tesseract (requires Poppler)
        try:
            images = convert_from_bytes(pdf_bytes)
        except Exception as e:
            # Bubble up a clear error so the UI can display an actionable message
            raise RuntimeError(
                "Unable to get page count. Is poppler installed and in PATH? Original error: " + str(e)
            )

        for image in images:
            # Use Tesseract to extract text, specifying languages
            try:
                content = pytesseract.image_to_string(image, lang=lang_str)
            except Exception:
                content = ""
            if content:
                text += content + "\n"  # Add a newline after each page's content
    return text

def get_chunk_text(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)

# -------------------- Embedding + Vector Store --------------------

def get_vector_store(text_chunks):
    # This now uses the multilingual model specified in your .env file
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    return FAISS.from_texts(texts=text_chunks, embedding=embeddings)

# -------------------- LLM Chain Setup (No changes needed here) --------------------

def get_conversation_chain(vector_store):
    # Read GROQ credentials at runtime (ensures Streamlit process loaded .env)
    api_key = os.environ.get("GROQ_API_KEY")
    model = os.environ.get("GROQ_MODEL_NAME") or groq_model_default

    # If GROQ is not configured, provide a simple local fallback that
    # returns the top retrieved document contents as the "answer" so the
    # app can be used for testing without an external LLM.
    if not api_key or not model:
        class SimpleConversation:
            def __init__(self, vector_store):
                self.vector_store = vector_store
                self.chat_history = []

            def invoke(self, inputs):
                question = inputs.get('question', '')
                answer = "I couldn't find a relevant passage in the documents."

                # Use FAISS similarity search directly to avoid retriever compatibility issues.
                try:
                    docs = self.vector_store.similarity_search(question, k=3)
                except Exception:
                    docs = []

                if docs:
                    answer = "\n\n".join([d.page_content for d in docs])
                else:
                    # Fall back to retriever if similarity_search is unavailable.
                    try:
                        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                        docs = retriever.get_relevant_documents(question)
                        if docs:
                            answer = "\n\n".join([d.page_content for d in docs])
                    except Exception:
                        pass

                self.chat_history.append({'question': question, 'answer': answer})
                return {'answer': answer, 'chat_history': self.chat_history}

        return SimpleConversation(vector_store)

    # Validate GROQ credentials and model before constructing the LLM.
    try:
        llm = ChatGroq(api_key=api_key, model=model, temperature=0)
        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    except Exception as e:
        # Show a clear warning in the UI and fall back to local retriever.
        try:
            st.warning(f"GROQ initialization failed: {e}. Falling back to local retriever.")
        except Exception:
            pass
        return create_simple_conversation(vector_store)

    system_template = """
    Use the following pieces of context and chat history to answer the question at the end.
    The context can be in any language. Answer the question based on the context.
    If you don't know the answer, just say you don't know, don't make anything up.

    Context: {context}
    Chat history: {chat_history}
    Question: {question}
    Helpful Answer:
    """

    prompt = PromptTemplate(
        template=system_template,
        input_variables=["context", "question", "chat_history"],
    )

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=True
    )
    return conversation_chain


def create_simple_conversation(vector_store):
    """Return a SimpleConversation fallback given a vector_store."""
    class SimpleConversation:
        def __init__(self, vector_store):
            self.vector_store = vector_store
            self.chat_history = []

        def invoke(self, inputs):
            question = inputs.get('question', '')
            answer = "I couldn't find a relevant passage in the documents."

            try:
                docs = self.vector_store.similarity_search(question, k=3)
            except Exception:
                docs = []

            if docs:
                answer = "\n\n".join([d.page_content for d in docs])
            else:
                try:
                    retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                    docs = retriever.get_relevant_documents(question)
                    if docs:
                        answer = "\n\n".join([d.page_content for d in docs])
                except Exception:
                    pass

            self.chat_history.append({'question': question, 'answer': answer})
            return {'answer': answer, 'chat_history': self.chat_history}

    return SimpleConversation(vector_store)

# -------------------- Chat Handler (No changes needed here) ----

def handle_user_input(question):
    try:
        response = st.session_state.conversation.invoke({'question': question})
        st.session_state.chat_history = response['chat_history']

        st.write(user_template.replace("{{MSG}}", question), unsafe_allow_html=True)
        st.write(bot_template.replace("{{MSG}}", response['answer']), unsafe_allow_html=True)

    except Exception as e:
        msg = str(e)
        # If the error looks like an auth/invalid API key error from GROQ, automatically fallback.
        if ('invalid_api_key' in msg.lower()) or ('invalid api key' in msg.lower()) or ('401' in msg):
            st.warning('GROQ authentication failed — falling back to local retriever for this session.')
            if 'vector_store' in st.session_state and st.session_state.vector_store is not None:
                st.session_state.conversation = create_simple_conversation(st.session_state.vector_store)
                try:
                    response = st.session_state.conversation.invoke({'question': question})
                    st.session_state.chat_history = response['chat_history']
                    st.write(user_template.replace("{{MSG}}", question), unsafe_allow_html=True)
                    st.write(bot_template.replace("{{MSG}}", response['answer']), unsafe_allow_html=True)
                    return
                except Exception as e2:
                    st.error(f"Fallback failed: {e2}")
                    return
            else:
                st.error('GROQ auth failed and no local vector store is available to fallback.')
                return
        st.error(f"Something went wrong: {e}")

# -------------------- UI (Modified for Language Selection) --------------------

def main():
    st.set_page_config(page_title='Chat with PDFs', page_icon='📄')
    st.write(css, unsafe_allow_html=True)
    st.header('📄 Chat with PDFs ')

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    question = st.text_input("Ask anything about your document(s):")

    if question:
        if st.session_state.conversation:
            handle_user_input(question)
        else:
            st.warning("⚠ Please upload and process PDF first.")

    with st.sidebar:
        st.subheader("Your Documents")
        # (debug removed) -- production: do not show secrets or internal config here
        
        # https://tesseract-ocr.github.io/tessdoc/Data-Files-in-version-4.00-information.html
        # Common Tesseract language codes
        available_langs = {
            "English": "eng", "Spanish": "spa", "French": "fra", 
            "German": "deu", "Chinese (Simplified)": "chi_sim", "Japanese": "jpn",
            "Korean": "kor", "Russian": "rus", "Hindi": "hin", "Arabic": "ara"
        }
        
        selected_languages = st.multiselect(
            "Select language(s) in the PDF:",
            options=list(available_langs.keys()),
            default=["English"]
        )
        
        pdf_files = st.file_uploader("Choose PDF(s) & press Process", type=['pdf'], accept_multiple_files=True)

        if pdf_files and st.button("Process"):
            if not selected_languages:
                st.warning("⚠ Please select at least one language.")
                return

            lang_codes = [available_langs[lang] for lang in selected_languages]

            with st.spinner("🔄 Processing PDFs with OCR... This may take a while."):
                try:
                    raw_text = get_pdf_text_with_ocr(pdf_files, lang_codes)
                    if not raw_text.strip():
                        st.error("❌ Could not extract text. The PDF might be empty or corrupted.")
                        return
                    
                    chunks = get_chunk_text(raw_text)
                    vector_store = get_vector_store(chunks)

                    # Save vector_store so we can fallback to a local retriever if the LLM auth fails
                    st.session_state.vector_store = vector_store

                    st.session_state.conversation = get_conversation_chain(vector_store)
                    st.success("✅ PDFs processed! You can now ask questions.")
                except Exception as e:
                    st.error(f"❌ Error while processing PDFs: {e}")

if __name__ == "__main__":
    main()
