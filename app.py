# Importing the necessary libarries
import os
import fitz  
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_bytes  
import pytesseract  
from groq import Groq  
from googleapiclient.discovery import build  

# Loading the environmental variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Streamlit page configuration 
st.set_page_config(
    page_title="Legal Document Simplifier",
    layout="wide",
    page_icon="⚖️"
)

# Custom CSS Styling 
st.markdown("""<style>...your CSS block...</style>""", unsafe_allow_html=True)


st.title("⚖️ Legal Document Simplifier")

-
# Initializing GROQ and Google Search API clients
if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
    st.warning("Invalid or missing GROQ_API_KEY. AI simplification will not work.")
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    st.warning("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID. Advisor search will not work.")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
search_service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# AI Simplification Function
def call_llama_groq(prompt):
    """Call the GROQ LLaMA-3 model with a user-defined prompt"""
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

# AI Q&A Function
def answer_question_about_document(question, document_text):
    """Uses LLaMA-3 to answer a question based only on the uploaded legal document"""
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

# PDF Text Extraction Function
def extract_text_from_pdf(uploaded_file):
    """Extracts text from PDF using PyMuPDF. If it fails, uses OCR as a fallback."""
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

# Google Search Function 
def google_search(query, num=5):
    """Performs a Google Custom Search for legal advisors"""
    if not search_service:
        return []
    try:
        result = search_service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num).execute()
        return result.get("items", [])
    except Exception as e:
        st.error(f"Google Search API error: {e}")
        return []

# Main App Logic 
def main():
    st.write("Upload a legal PDF document or paste legal text below, then click the button to simplify and get advisor recommendations.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
    with col2:
        text_input = st.text_area("Paste Legal Text Here", height=150)

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

        st.session_state.document_text = raw_text
        st.session_state.document_processed = True

        st.subheader("Original Input Preview")
        st.code(raw_text[:700] + ("..." if len(raw_text) > 700 else ""), language="text")

        prompt = f"""
The following is a {source} containing legal language:


{raw_text}


Please:
1. Summarize the document in plain English.
2. Highlight key legal points and implications.
3. Suggest next steps and legal considerations, in a professional tone.
"""

        with st.spinner("Analyzing legal document with AI..."):
            simplified = call_llama_groq(prompt)

        # Displaying the AI Output
        st.subheader("Simplified Summary")
        st.write(simplified)

        # Search for Legal Advisors 
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

    # Q&A Section for the uploaded document
    if st.session_state.document_processed and st.session_state.document_text:
        st.markdown("---")
        st.subheader("Ask Questions About Your Document")
        st.write("You can now ask specific questions about the document you uploaded or pasted.")

        # User Q&A input
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
            
            # Displaying the Q&A result
            st.markdown(f"""
            <div class="qa-section">
                <div class="question">{user_question}</div>
                <div class="answer">{answer}</div>
            </div>
            """, unsafe_allow_html=True)
        
        elif ask_button and not user_question.strip():
            st.error("Please enter a question before clicking 'Ask Question'.")

        # Suggested Questions
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

# Run the App 
if __name__ == "__main__":
    main()
