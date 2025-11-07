import streamlit as st
import io, json, uuid, os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient

# ----- CONFIG via environment variables -----
FR_ENDPOINT = os.environ["FR_ENDPOINT"]
FR_KEY = os.environ["FR_KEY"]
STORAGE_CONNECTION = os.environ["STORAGE_CONNECTION"]
STORAGE_CONTAINER = os.environ.get("STORAGE_CONTAINER", "resumes")
# --------------------------------------------

# Azure clients
doc_client = DocumentIntelligenceClient(FR_ENDPOINT, AzureKeyCredential(FR_KEY))
blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION)
container_client = blob_service.get_container_client(STORAGE_CONTAINER)

st.set_page_config(page_title="Resume Screening", layout="wide")
st.title("📄 Resume Screening (Azure Document Intelligence + Blob + Container Apps)")

with st.expander("ℹ️ How it works"):
    st.write(
        "- Upload a PDF resume\n"
        "- It’s sent to Azure Document Intelligence (prebuilt-document)\n"
        "- We compute a simple skill score\n"
        "- Original PDF + JSON result saved to Azure Blob"
    )

uploaded = st.file_uploader("Upload a PDF resume", type=["pdf"])

def analyze(pdf_bytes: bytes):
    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-document",
        body=io.BytesIO(pdf_bytes)
    )
    return poller.result()

if uploaded and st.button("Analyze"):
    pdf_bytes = uploaded.read()
    resume_id = str(uuid.uuid4())

    with st.spinner("Analyzing with Azure Document Intelligence..."):
        result = analyze(pdf_bytes)

    text = result.content or ""
    # very simple keyword scoring (customize this list)
    skills = ["python","java","c++","sql","aws","azure","ml","data","spring","django","fastapi","react"]
    hits = sum(s in text.lower() for s in skills)
    score = round(100 * hits / len(skills), 2)

    # Upload to Blob
    pdf_name = f"{resume_id}.pdf"
    json_name = f"{resume_id}.json"
    container_client.upload_blob(pdf_name, pdf_bytes, overwrite=True)
    container_client.upload_blob(
        json_name,
        json.dumps({
            "resumeId": resume_id,
            "score": score,
            "content": text
        }, ensure_ascii=False, indent=2).encode("utf-8"),
        overwrite=True
    )

    st.success("✅ Analyzed and stored in Blob Storage")
    st.metric("Score", f"{score}/100")

    st.subheader("Extracted text")
    st.text_area("Detected text", text, height=300)

    st.subheader("Blob objects")
    st.code(f"{STORAGE_CONTAINER}/{pdf_name}", language="text")
    st.code(f"{STORAGE_CONTAINER}/{json_name}", language="text")
