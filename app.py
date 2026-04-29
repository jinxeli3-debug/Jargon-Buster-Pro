import streamlit as st
import google.generativeai as genai
from docx import Document
from fpdf import FPDF
import io
import time

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
    
    st.caption("🔑 Need a key? [Get your free Gemini API key here](https://aistudio.google.com/app/apikey)")
    
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
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 12px;'>
            <strong>© 2026 Jargon Buster Pro</strong><br>
             All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- 4. MAIN UI & BASIC SETTINGS ---
st.title("Jargon Buster Pro 🚀")
st.caption("Master Teacher Edition: Smart Cache | 5E Rubrics | Bulk Run | COT Integration")

c1, c2, c3 = st.columns(3)
with c1:
    task_type = st.selectbox("Task?", ["General Simplify", "Unpack to 5E Lesson Plan"])
with c2:
    audience = st.selectbox("Audience?", ["Students", "Co-Teachers", "Master Teachers"])
with c3:
    target_lang = st.selectbox("Language?", ["English", "Tagalog", "Ilokano", "Pangasinan"])

# --- 5. MASTER TEACHER UPGRADES ---
st.write("---")
st.markdown("### 🌟 Master Teacher Upgrades")
col_mt1, col_mt2 = st.columns(2)

with col_mt1:
    needs_rubric = st.checkbox("📊 Include 4-Point Grading Rubric")
    needs_quiz = st.checkbox("📝 Generate 5-Item Quiz & Answer Key")
    local_context = st.text_input("🌴 Local Context (e.g., Binalonan Mango Farming, Tupig)")

with col_mt2:
    cot_indicators = st.multiselect("🎯 Select COT Indicators to Target", [
        "Indicator 1: Content knowledge and pedagogy",
        "Indicator 2: Literacy and numeracy skills",
        "Indicator 3: Critical and creative thinking (HOTS)",
        "Indicator 4: Meaningful exploration and hands-on activities",
        "Indicator 5: Constructive and positive discipline",
        "Indicator 6: Differentiated instruction for varied learners",
        "Indicator 7: Developmentally sequenced teaching",
        "Indicator 8: ICT integration",
        "Indicator 9: Formative and summative assessment"
    ])

# --- 6. PROMPT BUILDER HELPER ---
def build_advanced_prompt(base_melc):
    prompt = f"Target: {task_type}. Audience: {audience}. Language: {target_lang}. Text/MELC: {base_melc}."
    
    if task_type == "Unpack to 5E Lesson Plan":
        prompt += " Format strictly as a 5E Lesson Plan Markdown table."
    if needs_rubric:
        prompt += " Also include a 4-point grading rubric table at the bottom."
    if needs_quiz:
        prompt += " Append a 5-item multiple choice quiz based on the lesson, with a clear Answer Key at the very end."
    if local_context:
        prompt += f" Heavily contextualize the 'Engage' and 'Explore' phases around this local theme: {local_context}."
    if cot_indicators:
        prompt += f" Explicitly design the lesson to hit these COT indicators: {', '.join(cot_indicators)}. Add a brief 'COT Alignment Note' at the end explaining how they were met."
        
    return prompt

# --- 7. TABS LOGIC ---
st.write("---")
tab1, tab2 = st.tabs(["📄 Single Run", "📦 Bulk Run (Quarterly)"])

with tab1:
    text_to_bust = st.text_area("Paste a single text or MELC here:", height=150)
    
    if st.button("Process Single ✨", type="primary"):
        if not user_api_key or not text_to_bust:
            st.error("Please provide API Key and text!")
        else:
            try:
                final_prompt = build_advanced_prompt(text_to_bust)
                with st.spinner("Analyzing with Master Teacher protocols..."):
                    result_text = fetch_ai_response(final_prompt, user_api_key)
                    
                    st.toast("Done!", icon="✅")
                    st.session_state.history.append({"task": task_type, "result": result_text})
                    
                    st.markdown("---")
                    st.markdown(result_text)
                    
                    st.write("---")
                    colA, colB = st.columns(2)
                    with colA:
                        st.download_button("📥 Word (.docx)", convert_to_docx(result_text), "JargonBuster_Pro.docx", use_container_width=True)
                    with colB:
                        st.download_button("📄 PDF", convert_to_pdf(result_text), "JargonBuster_Pro.pdf", use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.info("💡 Paste multiple MELCs (one per line). All Master Teacher settings above will be applied to EVERY lesson.")
    bulk_text = st.text_area("Paste multiple MELCs here:", height=200, placeholder="MELC 1\nMELC 2\nMELC 3")
    
    if st.button("Process Bulk 📦", type="primary"):
        if not user_api_key or not bulk_text:
            st.error("Please provide API Key and text!")
        else:
            melcs_list = [m for m in bulk_text.split('\n') if m.strip() != '']
            final_bulk_document = "# 📦 Weekly Bulk Lesson Plan (COT Aligned)\n\n"
            progress_bar = st.progress(0)
            
            try:
                for i, melc in enumerate(melcs_list):
                    st.write(f"⏳ Processing: *{melc}*...")
                    final_prompt = build_advanced_prompt(melc)
                   
                    result_text = fetch_ai_response(final_prompt, user_api_key)
                    final_bulk_document += f"## Topic: {melc}\n{result_text}\n\n---\n\n"
                    progress_bar.progress((i + 1) / len(melcs_list))
                    
                    if i < len(melcs_list) - 1:
                        time.sleep(15) # Sleeps for 15 seconds to avoid the 5-per-minute limit
                
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