# whatsapp_async.py
import os
import logging
import asyncio
from typing import Optional
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v22.0")

if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_API_TOKEN:
    raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_API_TOKEN must be set in env vars.")

MEDIA_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/media"
MESSAGES_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
AUTH_HEADERS = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}


async def upload_media_bytes(
    client: httpx.AsyncClient,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> str:
    """
    Upload bytes as media to WhatsApp. Returns media id.
    """
    logger.info("Uploading media %s (%s) to WhatsApp", filename, mime_type)

    # Build multipart/form-data. The Graph API expects 'messaging_product' and the file field.
    # Using httpx, pass "files" param as tuples: (name, (filename, content, mime_type))
    files = {
        "file": (filename, file_bytes, mime_type),
    }
    data = {"messaging_product": "whatsapp", "type": mime_type}

    resp = await client.post(MEDIA_URL, headers=AUTH_HEADERS, files=files, data=data)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Media upload failed: %s - %s", resp.status_code, resp.text)
        raise

    body = resp.json()
    media_id = body.get("id")
    if not media_id:
        logger.error("Media upload response didn't include 'id': %s", body)
        raise RuntimeError("Media upload did not return an id.")

    logger.info("Uploaded media id=%s", media_id)
    return media_id


async def send_image_message(
    phone_number: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    image_url: Optional[str] = None,
    caption: Optional[str] = None,
) -> dict:
    """
    Send an image message to `phone_number`.
    Provide either `file_bytes`(and optional filename/mime_type) to upload first,
    or `image_url` to send by link.
    Returns the message endpoint response JSON.
    """
    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        close_client = True

    try:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            # we will set type below
        }

        if file_bytes is not None:
            # require filename and mime_type or infer simple defaults
            if not filename:
                filename = f"image_{int(asyncio.get_event_loop().time() * 1000)}.jpg"
            if not mime_type:
                mime_type = "image/jpeg"

            media_id = await upload_media_bytes(client, file_bytes, filename, mime_type)
            payload["type"] = "image"
            payload["image"] = {"id": media_id}
            if caption:
                payload["image"]["caption"] = caption

        elif image_url is not None:
            payload["type"] = "image"
            payload["image"] = {"link": image_url}
            if caption:
                payload["image"]["caption"] = caption

        else:
            raise ValueError("Either file_bytes or image_url must be provided.")

        headers = {"Content-Type": "application/json", **AUTH_HEADERS}
        logger.info("Sending message to %s: %s", phone_number, payload)
        resp = await client.post(MESSAGES_URL, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error("Failed to send message: %s - %s", resp.status_code, resp.text)
            raise

        logger.info("Message sent successfully to %s", phone_number)
        return resp.json()
    finally:
        if close_client:
            await client.aclose()
