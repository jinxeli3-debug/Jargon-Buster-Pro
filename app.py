import streamlit as st
import google.generativeai as genai
from docx import Document
from fpdf import FPDF
import io
import time
import pandas as pd # Needed for the Admin Dashboard charts

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

# --- 2. PAGE CONFIG & SaaS STATE ---
st.set_page_config(page_title="Jargon Buster Pro SaaS", page_icon="🚀", layout="wide")

# Simulated Database for the Principal Dashboard
if "history" not in st.session_state:
    st.session_state.history = []
if "cot_usage_stats" not in st.session_state:
    st.session_state.cot_usage_stats = {
        "Ind 1: Content": 0, "Ind 2: Literacy": 0, "Ind 3: HOTS": 0,
        "Ind 4: Exploration": 0, "Ind 5: Discipline": 0, "Ind 6: Differentiated": 0,
        "Ind 7: Sequenced": 0, "Ind 8: ICT": 0, "Ind 9: Assessment": 0
    }
# State for the Co-Pilot Chat
if "current_lesson" not in st.session_state:
    st.session_state.current_lesson = ""
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# --- 3. THE SIDEBAR (ROLE SELECTOR) ---
with st.sidebar:
    st.title("Settings ⚙️")
    user_role = st.radio("🔐 Login As:", ["Teacher", "Principal (Admin Dashboard)"])
    
    st.write("---")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    st.caption("🔑 [Get your free Gemini API key here](https://aistudio.google.com/app/apikey)")
    
    st.write("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 12px;'>
            <strong>© 2026 Jargon Buster Pro SaaS</strong><br>
            Developed by Eleazer A. Meriño<br>
            All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
#        PRINCIPAL (ADMIN) DASHBOARD
# ==========================================
if user_role == "Principal (Admin Dashboard)":
    st.title("📊 Principal's Analytics Dashboard")
    st.caption("School-wide overview of Jargon Buster Pro usage.")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Lessons Generated", len(st.session_state.history))
    c2.metric("Active Teachers", "1") # Hardcoded for now
    c3.metric("Most Used Context", "Binalonan Farming") # Hardcoded for now
    
    st.write("---")
    st.subheader("🎯 COT Indicator Targeting (School-wide)")
    st.caption("Tracks which indicators teachers are asking the AI to focus on.")
    
    # Generate a live chart from our simulated database
    chart_data = pd.DataFrame(
        list(st.session_state.cot_usage_stats.values()),
        index=list(st.session_state.cot_usage_stats.keys()),
        columns=["Times Targeted"]
    )
    st.bar_chart(chart_data)

# ==========================================
#              TEACHER VIEW
# ==========================================
else:
    st.title("Jargon Buster Pro 🚀")
    st.caption("Generate, Tweak, and Export 5E Lesson Plans instantly.")

    c1, c2, c3 = st.columns(3)
    task_type = c1.selectbox("Task?", ["Unpack to 5E Lesson Plan", "General Simplify"])
    audience = c2.selectbox("Audience?", ["Students", "Co-Teachers", "Master Teachers"])
    target_lang = c3.selectbox("Language?", ["English", "Tagalog", "Ilokano", "Pangasinan"])

    st.write("---")
    st.markdown("### 🌟 Lesson Parameters")
    col_mt1, col_mt2 = st.columns(2)

    with col_mt1:
        needs_rubric = st.checkbox("📊 Include 4-Point Grading Rubric")
        needs_quiz = st.checkbox("📝 Generate 5-Item Quiz & Answer Key")
        local_context = st.text_input("🌴 Local Context (e.g., Binalonan Mango Farming, Tupig)")

    with col_mt2:
        cot_indicators = st.multiselect("🎯 Select COT Indicators to Target", list(st.session_state.cot_usage_stats.keys()))

    text_to_bust = st.text_area("Paste a single text or MELC here:", height=100)
    
    if st.button("Generate Initial Lesson ✨", type="primary"):
        if not user_api_key or not text_to_bust:
            st.error("Please provide API Key and text!")
        else:
            prompt = f"Target: {task_type}. Audience: {audience}. Language: {target_lang}. Text: {text_to_bust}. Format as 5E plan."
            if needs_rubric: prompt += " Include grading rubric."
            if needs_quiz: prompt += " Include 5-item quiz."
            if local_context: prompt += f" Contextualize around: {local_context}."
            if cot_indicators: 
                prompt += f" Explicitly hit these COT indicators: {', '.join(cot_indicators)}."
                # Update Admin Database secretly!
                for ind in cot_indicators:
                    st.session_state.cot_usage_stats[ind] += 1

            with st.spinner("Drafting Master Teacher Lesson..."):
                result_text = fetch_ai_response(prompt, user_api_key)
                st.session_state.current_lesson = result_text
                st.session_state.history.append({"task": task_type, "result": result_text})
                # Reset chat when a new lesson is generated
                st.session_state.chat_messages = [] 
                st.rerun()

    # --- THE CO-PILOT EDITOR & EXPORT MODULE ---
    if st.session_state.current_lesson:
        st.write("---")
        st.subheader("📄 Your Generated Lesson Plan")
        
        # Display current document
        doc_container = st.container(border=True)
        doc_container.markdown(st.session_state.current_lesson)
        
        # EXPORT BUTTONS
        st.write("---")
        st.markdown("### 📥 Export Options")
        colA, colB, colC, colD = st.columns(4)
        colA.download_button("📄 Basic PDF", convert_to_pdf(st.session_state.current_lesson), "Lesson.pdf", use_container_width=True)
        colB.download_button("📄 Basic Word", convert_to_docx(st.session_state.current_lesson), "Lesson.docx", use_container_width=True)
        
        # Placeholders for future SaaS Features
        if colC.button("📊 Export to DepEd DLL (Excel)", use_container_width=True):
            st.info("Coming Soon: Requires uploading 'dll_template.xlsx' to GitHub.")
        if colD.button("🖥️ Generate PowerPoint", use_container_width=True):
            st.info("Coming Soon: Requires uploading 'slide_template.pptx' to GitHub.")

        # AI CO-PILOT CHAT
        st.write("---")
        st.markdown("### 🤖 Interactive Co-Pilot")
        st.caption("Tell the AI how to edit the document above (e.g., 'Make the quiz harder', 'Add more Ilokano translation').")
        
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        if edit_command := st.chat_input("How should we change the lesson plan?"):
            # Add user message to UI
            st.session_state.chat_messages.append({"role": "user", "content": edit_command})
            with st.chat_message("user"):
                st.markdown(edit_command)
                
            # Tell AI to edit the document
            with st.chat_message("assistant"):
                with st.spinner("Editing document..."):
                    edit_prompt = f"Here is a lesson plan:\n\n{st.session_state.current_lesson}\n\nUser request: {edit_command}\n\nRewrite the lesson plan incorporating this request."
                    new_doc = fetch_ai_response(edit_prompt, user_api_key)
                    st.session_state.current_lesson = new_doc
                    
                    st.markdown("Done! The document above has been updated.")
                    st.session_state.chat_messages.append({"role": "assistant", "content": "Done! The document above has been updated."})
                    time.sleep(1)
                    st.rerun() # Refresh the page to show the new document