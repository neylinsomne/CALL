"""
Webhook System for External Integrations
Allows external systems to subscribe to call center events
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx
from loguru import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ===========================================
# Models
# ===========================================

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]  # List of event types to subscribe to
    description: Optional[str] = None
    secret: Optional[str] = None  # Optional secret for signature verification


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    description: Optional[str]
    created_at: str
    active: bool


class WebhookEvent(BaseModel):
    event_type: str
    conversation_id: str
    data: dict
    timestamp: str


# ===========================================
# Webhook Storage (in-memory, use DB in production)
# ===========================================

webhooks: Dict[str, dict] = {}

# Supported event types
SUPPORTED_EVENTS = [
    "call_started",
    "call_ended",
    "turn_completed",
    "interruption",
    "transfer_requested",
    "callback_scheduled",
    "sentiment_alert",  # Triggered on frustrated/negative sentiment
    "error"
]


# ===========================================
# Webhook Management
# ===========================================

@router.post("/", response_model=WebhookResponse)
async def create_webhook(webhook: WebhookCreate):
    """Register a new webhook"""
    # Validate events
    invalid_events = [e for e in webhook.events if e not in SUPPORTED_EVENTS]
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid events: {invalid_events}. Supported: {SUPPORTED_EVENTS}"
        )

    webhook_id = str(uuid.uuid4())
    webhook_data = {
        "id": webhook_id,
        "url": str(webhook.url),
        "events": webhook.events,
        "description": webhook.description,
        "secret": webhook.secret,
        "created_at": datetime.utcnow().isoformat(),
        "active": True
    }

    webhooks[webhook_id] = webhook_data
    logger.info(f"Webhook created: {webhook_id} -> {webhook.url}")

    return WebhookResponse(**webhook_data)


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks():
    """List all registered webhooks"""
    return [
        WebhookResponse(**{k: v for k, v in w.items() if k != "secret"})
        for w in webhooks.values()
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str):
    """Get webhook by ID"""
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook = webhooks[webhook_id]
    return WebhookResponse(**{k: v for k, v in webhook.items() if k != "secret"})


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a webhook"""
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    del webhooks[webhook_id]
    logger.info(f"Webhook deleted: {webhook_id}")
    return {"status": "deleted", "webhook_id": webhook_id}


@router.patch("/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: str):
    """Enable/disable a webhook"""
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook = webhooks[webhook_id]
    webhook["active"] = not webhook["active"]
    status = "enabled" if webhook["active"] else "disabled"

    logger.info(f"Webhook {webhook_id} {status}")
    return {"status": status, "webhook_id": webhook_id, "active": webhook["active"]}


# ===========================================
# Event Triggering
# ===========================================

async def trigger_webhook_event(
    event_type: str,
    conversation_id: str,
    data: dict
):
    """
    Trigger webhooks subscribed to this event type
    This should be called from main.py when events occur
    """
    if event_type not in SUPPORTED_EVENTS:
        logger.warning(f"Unknown event type: {event_type}")
        return

    # Find webhooks subscribed to this event
    subscribed_webhooks = [
        w for w in webhooks.values()
        if w["active"] and event_type in w["events"]
    ]

    if not subscribed_webhooks:
        return

    event_payload = WebhookEvent(
        event_type=event_type,
        conversation_id=conversation_id,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )

    logger.info(f"Triggering {len(subscribed_webhooks)} webhooks for event: {event_type}")

    # Send webhook requests asynchronously
    tasks = [
        send_webhook_request(webhook, event_payload)
        for webhook in subscribed_webhooks
    ]

    # Fire and forget (don't block main flow)
    asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))


async def send_webhook_request(webhook: dict, event: WebhookEvent):
    """Send HTTP POST request to webhook URL"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Content-Type": "application/json"}

            # Add signature if secret is configured
            if webhook.get("secret"):
                import hmac
                import hashlib
                payload = event.json()
                signature = hmac.new(
                    webhook["secret"].encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = signature

            response = await client.post(
                webhook["url"],
                json=event.dict(),
                headers=headers
            )

            if response.status_code >= 400:
                logger.error(
                    f"Webhook {webhook['id']} failed: {response.status_code} - {response.text[:100]}"
                )
            else:
                logger.debug(f"Webhook {webhook['id']} delivered successfully")

    except Exception as e:
        logger.error(f"Webhook {webhook['id']} error: {e}")


# ===========================================
# Test Endpoint
# ===========================================

@router.post("/test/{webhook_id}")
async def test_webhook(webhook_id: str):
    """Send a test event to a webhook"""
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_event = WebhookEvent(
        event_type="test",
        conversation_id="test-conversation-id",
        data={"message": "This is a test webhook event"},
        timestamp=datetime.utcnow().isoformat()
    )

    await send_webhook_request(webhooks[webhook_id], test_event)

    return {"status": "test_sent", "webhook_id": webhook_id}
