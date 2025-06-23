import os
import uuid
from datetime import datetime, timedelta

from google.api_core import exceptions
from google.cloud import storage
from google.oauth2 import service_account  # updated
import io

SIGNED_URL_TTL_HOURS = 1  # Adjust if needed
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "agent-binod")
SERVICE_ACCOUNT_FILE = "/Users/simiknainwal/Documents/Emvo.AI/Hacko-ADK/agent/manager/tools/hacko.json"  # replace with your file name if different

# Create GCS client using service account
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
client = storage.Client(credentials=creds)

def upload_pdf_to_gcs(pdf_bytes: bytes, user_name: str) -> str:
    """
    Uploads PDF bytes to GCS and returns either:
      • a public URL  (if UBLA *off* and org-policy allows), or
      • a signed URL (if UBLA *on* or public access is blocked).
    """
    bucket = client.bucket(GCS_BUCKET_NAME)

    # Generate a safe, unique object name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in user_name if c.isalnum() or c in " -_").strip().replace(" ", "_")
    object_key = f"health_roadmaps/{safe_name}_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"

    blob = bucket.blob(object_key)
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")

    # Try public access first (only works if UBLA is off + org allows it)
    try:
        blob.make_public()
        return blob.public_url
    except (exceptions.Forbidden, exceptions.BadRequest):
        pass  # Fall back to signed URL

    # Generate signed URL
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=SIGNED_URL_TTL_HOURS),
        method="GET",
        response_disposition=f'attachment; filename="{safe_name}.pdf"',
        credentials=creds  # required for signing
    )
    return signed_url

# Example test runner
if __name__ == "__main__":
    from reportlab.pdfgen import canvas

    user_name = "Test User"
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "This is a test PDF for upload_pdf_to_gcs.")
    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    try:
        url = upload_pdf_to_gcs(pdf_bytes, user_name)
        print("✅ PDF uploaded! URL:", url)
    except Exception as e:
        print("❌ Error uploading PDF:", e)