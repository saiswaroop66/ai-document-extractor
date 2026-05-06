import streamlit as st
import pytesseract
from PIL import Image
import PyPDF2
import re
import spacy
import json
import pandas as pd

# -------------------------------
# 🔧 SAFE SPACY MODEL LOADER
# -------------------------------
@st.cache_resource
def load_model():
    try:
        return spacy.load("en_core_web_sm")
    except:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_model()

# -------------------------------
# 📄 PDF TEXT EXTRACTION
# -------------------------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

# -------------------------------
# 🖼️ IMAGE OCR
# -------------------------------
def extract_image_text(image):
    return pytesseract.image_to_string(image)

# -------------------------------
# 🧠 NLP + REGEX EXTRACTION
# -------------------------------
def extract_fields(text):
    doc = nlp(text)

    name, date, amount = None, None, None

    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON"] and not name:
            name = ent.text
        if ent.label_ == "DATE" and not date:
            date = ent.text

    amount_match = re.search(r'₹?\s?\d+(?:,\d{3})*(?:\.\d+)?', text)
    if amount_match:
        amount = amount_match.group()

    return {
        "name": name,
        "date": date,
        "amount": amount,
        "method": "Offline NLP"
    }

# -------------------------------
# 🎨 STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="AI Document Extractor", layout="wide")

st.title("📄 AI Document Extractor")
st.write("Upload PDF or Image → Extract Name, Date, Amount")

uploaded_file = st.file_uploader(
    "Upload Document",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    text = ""

    # PDF Handling
    if uploaded_file.type == "application/pdf":
        text = extract_pdf_text(uploaded_file)

    # Image Handling
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        text = extract_image_text(image)

    st.subheader("📜 Extracted Text")
    st.write(text[:2000])

    if st.button("🚀 Extract Data"):

        result = extract_fields(text)

        # -------------------------------
        # 📊 OUTPUT UI
        # -------------------------------
        st.subheader("📊 Extracted Data")

        col1, col2, col3 = st.columns(3)

        col1.metric("👤 Name", result.get("name", "N/A"))
        col2.metric("📅 Date", result.get("date", "N/A"))
        col3.metric("💰 Amount", result.get("amount", "N/A"))

        st.info(f"Method: {result.get('method')}")

        # Validation warning
        if not result.get("amount"):
            st.warning("⚠️ Amount not detected properly")

        # JSON View
        with st.expander("🔍 View Raw JSON"):
            st.json(result)

        # Table View
        df = pd.DataFrame([result])
        st.subheader("📋 Table View")
        st.table(df)

        # Download JSON
        json_data = json.dumps(result, indent=4)

        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="extracted_data.json",
            mime="application/json"
        )
