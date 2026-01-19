"""
Outbound Calling Service
API for initiating outbound AI calls via Asterisk
"""

import os
import uuid
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx


# ===========================================
# Configuration
# ===========================================
ASTERISK_ARI_URL = os.getenv("ASTERISK_ARI_URL", "http://asterisk:8088/ari")
ASTERISK_ARI_USER = os.getenv("ASTERISK_ARI_USER", "asterisk")
ASTERISK_ARI_PASSWORD = os.getenv("ASTERISK_ARI_PASSWORD", "asterisk")


# ===========================================
# Router
# ===========================================
router = APIRouter(prefix="/outbound", tags=["Outbound Calls"])


# ===========================================
# Models
# ===========================================
class OutboundCallRequest(BaseModel):
    phone_number: str
    caller_id: Optional[str] = None
    context: Optional[dict] = None  # Extra context for AI
    campaign_id: Optional[str] = None

class OutboundCallResponse(BaseModel):
    call_id: str
    conversation_id: str
    phone_number: str
    status: str
    initiated_at: str

class CallStatusResponse(BaseModel):
    call_id: str
    status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[list] = None


# ===========================================
# Active Calls Store
# ===========================================
active_calls = {}


# ===========================================
# Endpoints
# ===========================================
@router.post("/call", response_model=OutboundCallResponse)
async def initiate_outbound_call(request: OutboundCallRequest):
    """
    Initiate an outbound AI call
    
    The AI will call the specified number and start a conversation.
    """
    call_id = str(uuid.uuid4())
    conversation_id = f"outbound-{call_id}"
    
    try:
        # Originate call via Asterisk ARI
        async with httpx.AsyncClient() as client:
            # Create channel
            response = await client.post(
                f"{ASTERISK_ARI_URL}/channels",
                auth=(ASTERISK_ARI_USER, ASTERISK_ARI_PASSWORD),
                params={
                    "endpoint": f"PJSIP/{request.phone_number}@trunk-endpoint",
                    "extension": "s",
                    "context": "outbound-connect",
                    "priority": 1,
                    "callerId": request.caller_id or os.getenv("OUTBOUND_CALLERID", "AI Call Center"),
                    "timeout": 60,
                    "variables": {
                        "CONVERSATION_ID": conversation_id,
                        "CAMPAIGN_ID": request.campaign_id or ""
                    }
                }
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to originate call: {response.text}"
                )
            
            channel_data = response.json()
            
        # Store call info
        active_calls[call_id] = {
            "call_id": call_id,
            "conversation_id": conversation_id,
            "phone_number": request.phone_number,
            "status": "dialing",
            "initiated_at": datetime.utcnow().isoformat(),
            "channel_id": channel_data.get("id"),
            "context": request.context
        }
        
        return OutboundCallResponse(
            call_id=call_id,
            conversation_id=conversation_id,
            phone_number=request.phone_number,
            status="dialing",
            initiated_at=active_calls[call_id]["initiated_at"]
        )
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


@router.get("/call/{call_id}", response_model=CallStatusResponse)
async def get_call_status(call_id: str):
    """Get the status of an outbound call"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call = active_calls[call_id]
    
    # Get channel status from Asterisk
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ASTERISK_ARI_URL}/channels/{call['channel_id']}",
                auth=(ASTERISK_ARI_USER, ASTERISK_ARI_PASSWORD)
            )
            
            if response.status_code == 200:
                channel = response.json()
                call["status"] = channel.get("state", "unknown")
            elif response.status_code == 404:
                call["status"] = "ended"
                
    except Exception:
        pass  # Use cached status
    
    return CallStatusResponse(
        call_id=call_id,
        status=call["status"],
        duration_seconds=None,
        transcript=None
    )


@router.delete("/call/{call_id}")
async def hangup_call(call_id: str):
    """Hangup an active call"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call = active_calls[call_id]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{ASTERISK_ARI_URL}/channels/{call['channel_id']}",
                auth=(ASTERISK_ARI_USER, ASTERISK_ARI_PASSWORD)
            )
            
        call["status"] = "ended"
        return {"status": "Call terminated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign")
async def start_campaign(
    phone_numbers: list,
    campaign_id: Optional[str] = None,
    caller_id: Optional[str] = None,
    concurrent_calls: int = 5,
    delay_between_calls: float = 1.0
):
    """
    Start a campaign with multiple outbound calls
    
    Args:
        phone_numbers: List of phone numbers to call
        campaign_id: Optional campaign identifier
        concurrent_calls: Max concurrent calls
        delay_between_calls: Seconds between initiating calls
    """
    campaign_id = campaign_id or str(uuid.uuid4())
    results = []
    
    semaphore = asyncio.Semaphore(concurrent_calls)
    
    async def call_number(phone: str):
        async with semaphore:
            try:
                result = await initiate_outbound_call(
                    OutboundCallRequest(
                        phone_number=phone,
                        caller_id=caller_id,
                        campaign_id=campaign_id
                    )
                )
                results.append({"phone": phone, "status": "initiated", "call_id": result.call_id})
            except Exception as e:
                results.append({"phone": phone, "status": "failed", "error": str(e)})
            
            await asyncio.sleep(delay_between_calls)
    
    # Start all calls
    await asyncio.gather(*[call_number(phone) for phone in phone_numbers])
    
    return {
        "campaign_id": campaign_id,
        "total_numbers": len(phone_numbers),
        "initiated": len([r for r in results if r["status"] == "initiated"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "results": results
    }


@router.get("/active")
async def list_active_calls():
    """List all active outbound calls"""
    return {
        "active_calls": len(active_calls),
        "calls": list(active_calls.values())
    }
