import logging
import azure.functions as func
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import io, uuid, json, os

FR_ENDPOINT = os.environ["FR_ENDPOINT"]
FR_KEY = os.environ["FR_KEY"]
STORAGE_CONNECTION = os.environ["STORAGE_CONNECTION"]
CONTAINER = "resumes"

doc_client = DocumentIntelligenceClient(FR_ENDPOINT, AzureKeyCredential(FR_KEY))
blob_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION)
container_client = blob_client.get_container_client(CONTAINER)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        file = req.files["file"].read()

        resume_id = str(uuid.uuid4())

        poller = doc_client.begin_analyze_document(
            model_id="prebuilt-read",
            body=io.BytesIO(file)
        )
        result = poller.result()
        text = result.content or ""

        skills = ["python","java","c++","sql","aws","azure","ml","data","spring","django","fastapi","react"]
        hits = sum(s in text.lower() for s in skills)
        score = round(100 * hits / len(skills), 2)

        container_client.upload_blob(f"{resume_id}.pdf", file, overwrite=True)

        container_client.upload_blob(
            f"{resume_id}.json",
            json.dumps({"resumeId": resume_id, "score": score, "content": text}, indent=2),
            overwrite=True
        )

        return func.HttpResponse(
            json.dumps({"resumeId": resume_id, "score": score, "content": text}),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(e)
        return func.HttpResponse(str(e), status_code=500)
