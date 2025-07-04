import os
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
import pytesseract
from groq import Groq
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

st.set_page_config(
    page_title="Legal Document Simplifier",
    layout="wide",
    page_icon="⚖️"
)

# Enhanced CSS with vibrant colors and modern styling
st.markdown("""
<style>
/* Main title styling */
h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    font-size: 2.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

/* Main app background */
.main .block-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 15px;
    padding: 2rem;
    margin-top: 1rem;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 0.8rem 2rem;
    border-radius: 25px;
    border: none;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    font-size: 1.1rem;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* File uploader styling */
.uploadedFile {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    border-radius: 10px;
    padding: 1rem;
    border: 2px dashed #667eea;
}

/* Text area styling */
.stTextArea > div > div > textarea {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border: 2px solid #ff9a9e;
    border-radius: 15px;
    color: #333;
    font-weight: 500;
}

/* Q&A section styling */
.qa-section {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1.5rem;
    border-radius: 15px;
    border-left: 6px solid #667eea;
    margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.qa-section:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.question {
    font-weight: 700;
    color: #667eea;
    margin-bottom: 0.8rem;
    font-size: 1.1rem;
}
.answer {
    color: #4a5568;
    line-height: 1.7;
    font-size: 1rem;
    background: rgba(255,255,255,0.7);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #ff9a9e;
}

/* Subheader styling */
h2, h3 {
    color: #667eea;
    border-bottom: 2px solid #ff9a9e;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Info boxes */
.stInfo {
    background: linear-gradient(135deg, #d299c2 0%, #fef9d3 100%);
    border-radius: 10px;
    border-left: 4px solid #667eea;
}

/* Warning boxes */
.stWarning {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border-radius: 10px;
    border-left: 4px solid #ff9a9e;
}

/* Error boxes */
.stError {
    background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
    border-radius: 10px;
    border-left: 4px solid #e17055;
}

/* Success boxes */
.stSuccess {
    background: linear-gradient(135deg, #b7f8db 0%, #50fa7b 100%);
    border-radius: 10px;
    border-left: 4px solid #00b894;
}

/* Code blocks */
.stCodeBlock {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
    border-radius: 10px;
    border: 2px solid #667eea;
}

/* Suggested questions buttons */
div[data-testid="column"] .stButton > button {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    color: #333;
    font-weight: 600;
    padding: 0.6rem 1rem;
    border-radius: 20px;
    border: 2px solid #ff9a9e;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

div[data-testid="column"] .stButton > button:hover {
    background: linear-gradient(135deg, #fecfef 0%, #ff9a9e 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3);
}

/* Text input styling */
.stTextInput > div > div > input {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border: 2px solid #ff9a9e;
    border-radius: 15px;
    color: #333;
    font-weight: 500;
    padding: 0.8rem;
}

/* Spinner styling */
.stSpinner > div {
    border-top-color: #667eea !important;
}

/* Markdown links */
a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}
a:hover {
    color: #764ba2;
    text-decoration: underline;
}

/* Columns styling */
div[data-testid="column"] {
    padding: 0.5rem;
}

/* Section dividers */
hr {
    border: none;
    height: 3px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 2px;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Legal Document Simplifier")

if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.warning("Invalid or missing GROQ_API_KEY. AI simplification will not work.")
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.warning("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID. Advisor search will not work.")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
search_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

def call_llama_groq(prompt):
    if not client:
        return "GROQ API key missing, cannot process request."
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a friendly AI legal assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling GROQ API: {e}"

def answer_question_about_document(question, document_text):
    """
    Answer a specific question about the given document using AI
    """
    if not client:
        return "GROQ API key missing, cannot answer questions."
    
    prompt = f"""
You are a legal assistant helping to answer questions about a specific legal document.

Here is the document content:
=== DOCUMENT START ===
{document_text}
=== DOCUMENT END ===

Question: {question}

Please provide a clear, accurate answer based solely on the information in the document above. If the document doesn't contain enough information to answer the question, please say so. Be specific and cite relevant sections when possible.

Answer:"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful legal assistant who answers questions based strictly on the provided document content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error answering question: {e}"

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        if text.strip():
            return text
    except Exception:
        pass

    st.info("No text detected in PDF — performing OCR...")
    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return ocr_text
    except Exception as e:
        st.error(f"OCR failed: {e}")
        return ""

def google_search(query, num=5):
    if not search_service:
        return []
    try:
        result = search_service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num).execute()
        return result.get("items", [])
    except Exception as e:
        st.error(f"Google Search API error: {e}")
        return []

def main():
    st.write("Upload a legal PDF document or paste legal text below, then click the button to simplify and get advisor recommendations.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
    with col2:
        text_input = st.text_area("Paste Legal Text Here", height=150)

    # Initialize session state for document text
    if 'document_text' not in st.session_state:
        st.session_state.document_text = ""
    if 'document_processed' not in st.session_state:
        st.session_state.document_processed = False

    if st.button("Simplify & Recommend Advisor"):
        if not uploaded_file and not text_input.strip():
            st.error("Please upload a PDF or enter legal text to continue.")
            return

        raw_text = ""
        source = ""
        if uploaded_file:
            source = "PDF document"
            with st.spinner("Extracting text from PDF..."):
                raw_text = extract_text_from_pdf(uploaded_file)
            if not raw_text.strip():
                st.error("Failed to extract any text from the PDF.")
                return
        else:
            source = "text input"
            raw_text = text_input.strip()

        # Store document text in session state
        st.session_state.document_text = raw_text
        st.session_state.document_processed = True

        st.subheader("Original Input Preview")
        st.code(raw_text[:700] + ("..." if len(raw_text) > 700 else ""), language="text")

        prompt = f"""
The following is a {source} containing legal language:

=== START ===
{raw_text}
=== END ===

Please:
1. Summarize the document in plain English.
2. Highlight key legal points and implications.
3. Suggest next steps and legal considerations, in a professional tone.
"""

        with st.spinner("Analyzing legal document with AI..."):
            simplified = call_llama_groq(prompt)

        st.subheader("Simplified Summary")
        st.write(simplified)

        st.subheader("Recommended Legal Advisors")
        query = "legal advisor near me for contract law"
        with st.spinner("Searching for legal advisors..."):
            results = google_search(query, num=5)

        if results:
            for item in results:
                title = item.get("title")
                snippet = item.get("snippet")
                link = item.get("link")
                st.markdown(f"**[{title}]({link})**  \n{snippet}")
        else:
            st.info("No legal advisors found or missing Google API keys.")

    # Q&A Section - only show if document has been processed
    if st.session_state.document_processed and st.session_state.document_text:
        st.markdown("---")
        st.subheader("Ask Questions About Your Document")
        st.write("You can now ask specific questions about the document you uploaded or pasted.")
        
        # Question input
        user_question = st.text_input(
            "Enter your question about the document:",
            placeholder="e.g., What are the key obligations mentioned in this contract?",
            key="question_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            ask_button = st.button("Ask Question", key="ask_btn")
        
        if ask_button and user_question.strip():
            with st.spinner("Analyzing document to answer your question..."):
                answer = answer_question_about_document(user_question, st.session_state.document_text)
            
            # Display Q&A in a styled format
            st.markdown(f"""
            <div class="qa-section">
                <div class="question">{user_question}</div>
                <div class="answer">{answer}</div>
            </div>
            """, unsafe_allow_html=True)
        
        elif ask_button and not user_question.strip():
            st.error("Please enter a question before clicking 'Ask Question'.")
        
        # Common question suggestions
        st.markdown("**Suggested Questions:**")
        suggested_questions = [
            "What are the main parties involved in this document?",
            "What are the key terms and conditions?",
            "What are the important dates or deadlines mentioned?",
            "What are the payment terms or financial obligations?",
            "What happens if there's a breach of contract?",
            "Are there any termination clauses?",
            "What are the governing laws mentioned?"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(suggested_questions):
            with cols[i % 2]:
                if st.button(question, key=f"suggested_{i}"):
                    with st.spinner("Analyzing document to answer your question..."):
                        answer = answer_question_about_document(question, st.session_state.document_text)
                    
                    st.markdown(f"""
                    <div class="qa-section">
                        <div class="question">❓ {question}</div>
                        <div class="answer">💡 {answer}</div>
                    </div>
                    """, unsafe_allow_html=True)

    elif not st.session_state.document_processed:
        st.info("Upload a document and click 'Simplify & Recommend Advisor' first to enable the Q&A feature.")

if __name__ == "__main__":
    main()