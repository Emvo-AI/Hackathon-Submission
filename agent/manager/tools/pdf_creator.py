# ───────────────────────────────────────────────────────────────
# PdfCreatorTool – functional tool for Google-ADK auto-calling
# ───────────────────────────────────────────────────────────────
# pip install reportlab
# Place this file in your tools/ directory and make sure the
# package is import-scanned by ADK (e.g. listed in __init__.py).
# Sub-agents can now invoke   PdfCreatorTool(plan_summary=..., user_info=...)
# and the ADK runtime will call this function automatically.
# ───────────────────────────────────────────────────────────────

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timedelta
import base64, io, re
import os
import uuid
import logging
from google.api_core import exceptions
from google.cloud import storage
from google.oauth2 import service_account 

# Setup logging to logs.txt in the same directory as this file
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs.txt")
logging.basicConfig(
    filename=LOG_FILE_PATH,
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from google.cloud import storage
    from google.auth import default
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not available. PDF upload to GCS will be disabled.")

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib.units import mm
from pydantic import BaseModel, Field

# ─────────────── visual theme vars (tweak freely) ──────────────
PRIMARY      = colors.HexColor("#4C7CF3")
TEXT_DARK    = colors.HexColor("#1A1A1A")
LOGO_PATH    = None            # e.g. "assets/emvo_logo.png"
TITLE_FONT   = "Helvetica-Bold"
BODY_FONT    = "Helvetica"

# Google Cloud Storage configuration
SIGNED_URL_TTL_HOURS = 1  # Adjust if needed
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "agent-binod")
SERVICE_ACCOUNT_FILE = "/Users/abhay/EMVO/Hacko/Hacko-ADK/agent/manager/tools/hacko.json"  # replace with your file name if different
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
client = storage.Client(credentials=creds)

# ───────────────────────── schema ──────────────────────────────
class PdfArgs(BaseModel):
    """Arguments required by PdfCreatorTool."""
    plan_summary: str = Field(
        description="Full guideline text in lightweight markdown "
                    "(supports **bold**, **Heading**, and • / - bullet lines)."
    )
    user_info: Dict[str, Any] = Field(
        description="Dictionary with at least `name` and `location` keys; "
                    "extra keys (e.g. goals) are ignored."
    )

# Constants (ensure these are set somewhere in your app)
GCS_AVAILABLE = True
GCS_PROJECT_ID = "onyx-syntax-451614-t2"
GCS_BUCKET_NAME = "agent-binod"

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


def pdf_creator_tool(plan_summary: str, user_info: Dict[str, Any]) -> str:
    """  Generate a polished, branded PDF roadmap (dietary or lifestyle guidance)
    based on a lightweight markdown-style summary and user metadata.

    Args:  
        plan_summary: str -> Plain-text guideline supporting **bold**, **Heading**, and bullet
            lines (– or •). This is the full content to render in the PDF.
        user_info: object -> Dictionary containing at least:
            • name (string): User's display name  
            • location (string): User's locale  
        Additional keys (e.g. goals) may be included and will be ignored or
        optionally rendered in the metadata header.
        
    Returns str ->    Public URL to the uploaded PDF in Google Cloud Storage, or base64-encoded PDF
    if GCS upload fails.
."""
    logger.info(f"pdf_creator_tool called with user_info: {user_info}")
    # ----- style helpers ----------------------------------------------------
    def build_styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            "TitleBar", fontName=TITLE_FONT, fontSize=22, leading=26,
            textColor=colors.white, alignment=1))
        styles.add(ParagraphStyle(
            "SectionHeader", fontName=TITLE_FONT, fontSize=14, leading=18,
            textColor=PRIMARY, spaceAfter=6))
        styles["BodyText"].fontName  = BODY_FONT
        styles["BodyText"].fontSize  = 11
        styles["BodyText"].leading   = 15
        styles["BodyText"].textColor = TEXT_DARK
        return styles

    # ----- header bar -------------------------------------------------------
    def add_title_bar(elm, sty):
        title = Paragraph("Personalised Health Roadmap", sty["TitleBar"])
        tbl   = Table([[title]], colWidths=[170*mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), PRIMARY),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
            ("LEFTPADDING",(0,0), (-1,-1), 0),
            ("RIGHTPADDING",(0,0),(-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]))
        if LOGO_PATH:
            logo = Image(LOGO_PATH, width=25*mm, height=25*mm, hAlign="LEFT")
            row  = Table([[logo, tbl]], colWidths=[30*mm, 140*mm])
            row.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
            elm.append(row)
        else:
            elm.append(tbl)
        elm.append(Spacer(1, 6))
        meta = Paragraph(
            f"<b>Name:</b> {user_info.get('name','User')} &nbsp;&nbsp; "
            f"<b>Location:</b> {user_info.get('location','Unknown')} &nbsp;&nbsp; "
            f"<b>Date:</b> {datetime.utcnow():%d %b %Y}",
            sty["BodyText"])
        elm.append(meta)
        elm.append(Spacer(1, 12))

    # ----- miniature markdown-ish parser -----------------------------------
    section_rx = re.compile(r"^\*\*(.+?)\*\*$")
    bold_rx    = re.compile(r"\*\*(.+?)\*\*")
    list_rx    = re.compile(r"^[-•]\s+(.*)$")

    def summary_to_flowables(text: str, sty):
        out = []
        for raw in text.splitlines():
            ln = raw.strip()
            if not ln:
                out.append(Spacer(1, 6)); continue
            if (m:=section_rx.match(ln)):
                out.append(Paragraph(m.group(1), sty["SectionHeader"])); continue
            if (m:=list_rx.match(ln)):
                item = "• " + bold_rx.sub(r"<b>\1</b>", m.group(1))
                out.append(Paragraph(item, sty["BodyText"])); continue
            out.append(Paragraph(bold_rx.sub(r"<b>\1</b>", ln), sty["BodyText"]))
        return out

    # ----- build PDF in memory ---------------------------------------------
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm,
        title="Personalised Health Roadmap", author="Emvo AI",
    )
    style = build_styles()
    elements = []
    add_title_bar(elements, style)
    elements += summary_to_flowables(plan_summary, style)
    elements.append(Spacer(1, 12))
    footer = Paragraph(
        "<font size=9 color='#777777'>Generated by Emvo AI — not a substitute "
        "for professional medical advice.</font>",
        style["BodyText"])
    elements.append(footer)
    try:
        doc.build(elements)
        logger.info("PDF document built successfully in memory.")
    except Exception as e:
        logger.error(f"Error building PDF document: {str(e)}")
        raise

    # ----- get PDF bytes ---------------------------------------------------
    pdf_bytes = buf.getvalue()
    buf.close()
    logger.info(f"PDF bytes generated. Size: {len(pdf_bytes)} bytes.")
    
    # ----- try to upload to GCS and return URL ----------------------------
    try:
        if GCS_AVAILABLE and GCS_BUCKET_NAME:
            user_name = user_info.get('name', 'User')
            logger.info(f"Attempting to upload PDF to GCS for user: {user_name}")
            public_url = upload_pdf_to_gcs(pdf_bytes, user_name)
            logger.info(f"PDF successfully uploaded. Public URL: {public_url}")
            return public_url
        else:
            # Fallback to base64 if GCS is not available
            logger.warning("GCS not available or bucket name missing. Returning base64 encoded PDF.")
            encoded = base64.b64encode(pdf_bytes).decode("utf-8")
            return encoded
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {str(e)}. Returning base64 encoded PDF.")
        # Fallback to base64 encoding
        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        return encoded


if __name__ == "__main__":
    # Example usage
    plan_summary = """
    **Dietary Guidelines**
    • Eat more fruits and vegetables
    • Drink plenty of water
    **Exercise Recommendations**
    • Aim for at least 30 minutes of moderate exercise daily
    """
    
    user_info = {
        "name": "John Doe",
        "location": "New York, USA"
    }
    
    pdf_url = pdf_creator_tool(plan_summary, user_info)
    print("Generated PDF URL or base64:", pdf_url)