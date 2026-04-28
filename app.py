import streamlit as st
import google-generativeai as genai
from docx import Document
from fpdf import FPDF
import io
import time # Added to prevent Bulk Run from crashing the Free Tier

# --- 1. CORE FUNCTIONS & CACHING ---
def convert_to_docx(text):
    doc = Document()
    doc.add_heading('Jargon Buster Pro - DepEd Report', 0)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def convert_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return bytes(pdf.output())

# FEATURE 1: Smart Caching (Saves API Quota!)
# The underscore in _api_key tells Streamlit to only memorize the prompt, keeping your key secure.
@st.cache_data(show_spinner=False)
def fetch_ai_response(prompt_text, _api_key):
    genai.configure(api_key=_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt_text)
    return response.text

# --- 2. PAGE CONFIG & STATE ---
st.set_page_config(page_title="Jargon Buster Pro", page_icon="🚀", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

# --- 3. THE SIDEBAR ---
with st.sidebar:
    st.title("Settings ⚙️")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.write("---")
    st.markdown("### 👨‍🏫 Developer")
    st.write("**Name:** Eleazer A. Meriño")
    st.write("DepEd Proficient Teacher | Lone Developer")
    
    st.write("---")
    st.markdown("### 🗂️ Cache & History")
    if len(st.session_state.history) == 0:
        st.caption("No history yet.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Run {len(st.session_state.history) - i}: {item['task']}"):
                st.write(item['result'][:150] + "...")
                
    st.write("---")
    st.link_button("📧 Contact Support", "mailto:your.email@deped.gov.ph", use_container_width=True)
    st.caption("© 2026 Eleazer A. Meriño | Jargon Buster Pro")

# --- 4. MAIN UI & SETTINGS ---
st.title("Jargon Buster Pro 🚀")
st.caption("God-Tier Edition: Smart Cache | 5E Rubrics | Bulk Processing")

# Global Settings for both tabs
c1, c2, c3 = st.columns(3)
with c1:
    task_type = st.selectbox("Task?", ["General Simplify", "Unpack to 5E Lesson Plan"])
with c2:
    audience = st.selectbox("Audience?", ["Students", "Co-Teachers", "Master Teachers"])
with c3:
    target_lang = st.selectbox("Language?", ["English", "Tagalog", "Ilokano", "Pangasinan"])

# FEATURE 2: The Automated Rubric Generator
needs_rubric = st.checkbox("📊 Include 4-Point Grading Rubric (For 5E Evaluation Phase)")

# --- 5. TABS LOGIC (Single vs Bulk) ---
tab1, tab2 = st.tabs(["📄 Single Run", "📦 Bulk Run (Quarterly)"])

with tab1:
    text_to_bust = st.text_area("Paste a single text or MELC here:", height=250)
    
    if st.button("Process Single ✨", type="primary"):
        if not user_api_key or not text_to_bust:
            st.error("Please provide API Key and text!")
        else:
            try:
                # Build Prompt
                prompt = f"Target: {task_type}. Audience: {audience}. Language: {target_lang}. Text/MELC: {text_to_bust}."
                if task_type == "Unpack to 5E Lesson Plan":
                    prompt += " Format strictly as a 5E Lesson Plan Markdown table."
                if needs_rubric:
                    prompt += " Also include a 4-point grading rubric table at the bottom."
                
                with st.spinner("Analyzing (or loading from Cache)..."):
                    # Calling the cached function!
                    result_text = fetch_ai_response(prompt, user_api_key)
                    
                    st.toast("Done!", icon="✅")
                    st.session_state.history.append({"task": task_type, "result": result_text})
                    
                    st.markdown("---")
                    st.markdown(result_text)
                    
                    st.write("---")
                    colA, colB = st.columns(2)
                    with colA:
                        st.download_button("📥 Word (.docx)", convert_to_docx(result_text), "JargonBuster.docx", use_container_width=True)
                    with colB:
                        st.download_button("📄 PDF", convert_to_pdf(result_text), "JargonBuster.pdf", use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

# FEATURE 3: Bulk Processing
with tab2:
    st.info("💡 Paste multiple MELCs (one per line) to generate a massive weekly plan.")
    bulk_text = st.text_area("Paste multiple MELCs here:", height=250, placeholder="MELC 1\nMELC 2\nMELC 3")
    
    if st.button("Process Bulk 📦", type="primary"):
        if not user_api_key or not bulk_text:
            st.error("Please provide API Key and text!")
        else:
            melcs_list = [m for m in bulk_text.split('\n') if m.strip() != '']
            final_bulk_document = "# 📦 Weekly Bulk Lesson Plan\n\n"
            
            # Progress bar for visual feedback
            progress_bar = st.progress(0)
            
            try:
                for i, melc in enumerate(melcs_list):
                    st.write(f"⏳ Processing: *{melc}*...")
                    
                    # Build Prompt for this specific MELC
                    prompt = f"Target: {task_type}. Audience: {audience}. Language: {target_lang}. Text/MELC: {melc}."
                    if task_type == "Unpack to 5E Lesson Plan":
                        prompt += " Format strictly as a 5E Lesson Plan Markdown table."
                    if needs_rubric:
                        prompt += " Include a 4-point grading rubric table."
                        
                    # Fetch from cache or API
                    result_text = fetch_ai_response(prompt, user_api_key)
                    final_bulk_document += f"## Topic: {melc}\n{result_text}\n\n---\n\n"
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / len(melcs_list))
                    
                    # Breath to avoid 429 Error on Free Tier
                    if i < len(melcs_list) - 1:
                        time.sleep(3) 
                
                st.toast("Bulk Processing Complete!", icon="🎉")
                st.session_state.history.append({"task": "Bulk Run", "result": final_bulk_document})
                
                st.success("All MELCs processed! Ready for export.")
                st.markdown(final_bulk_document)
                
                st.write("---")
                colA, colB = st.columns(2)
                with colA:
                    st.download_button("📥 Download Bulk Word", convert_to_docx(final_bulk_document), "Bulk_Lessons.docx", use_container_width=True)
                with colB:
                    st.download_button("📄 Download Bulk PDF", convert_to_pdf(final_bulk_document), "Bulk_Lessons.pdf", use_container_width=True)
            except Exception as e:
                st.error(f"Error during bulk run: {e}")