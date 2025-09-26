import chainlit as cl
import requests
import io
import docx
import pypdf
import pathway as pw
import json

# -----------------------------
# Gemini API Setup
# -----------------------------
LLM_API_KEY = "AIzaSyAtZRbuwrmUGb9RvkiFGfGgcdANmf511Gs"  # replace with your key
LLM_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

# --- Extractors ---
def extract_text_from_pdf(file_bytes):
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)

# --- LLM call ---
def generate_report(document_text, instructions):
    prompt = f"""
Generate a structured and concise report based on the following document content and user instructions. 
The report must be evidence-based and cite specific parts of the text. Format using markdown.

Document:
---
{document_text}
---

Instructions:
{instructions}

Include a "Citations" section at the end.
"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(f"{LLM_ENDPOINT}?key={LLM_API_KEY}",
                             headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    data = response.json()
    return data['candidates'][0]['content']['parts'][0]['text']

# --- Chat handler ---
@cl.on_message
async def handle_message(msg: cl.Message):
    if not msg.elements:
        await cl.Message("📎 Please upload a PDF or DOCX file.").send()
        return

    for elem in msg.elements:
        file_bytes = elem.content or open(elem.path, "rb").read()
        
        if elem.mime == "application/pdf":
            text = extract_text_from_pdf(file_bytes)
        elif elem.mime in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]:
            text = extract_text_from_docx(file_bytes)
        else:
            await cl.Message("❌ Unsupported file type. Please upload PDF or DOCX.").send()
            return

        report = generate_report(text, msg.content)
        await cl.Message(report).send()

