"""
AI Call Center - Backend API
FastAPI application with WebSocket support for real-time voice processing
"""

import os
import uuid
import asyncio
import json
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

from database import Database, Conversation, Message
from websocket_manager import ConnectionManager
from outbound import router as outbound_router
from vocabulary import router as vocabulary_router


# ===========================================
# Configuration
# ===========================================
TTS_URL = os.getenv("TTS_URL", "http://tts:8001")
STT_URL = os.getenv("STT_URL", "http://stt:8002")
LLM_URL = os.getenv("LLM_URL", "http://llm:8003")
GREETING = os.getenv("CALL_CENTER_GREETING", "Hola, bienvenido. ¿En qué puedo ayudarle?")


# ===========================================
# Lifespan
# ===========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="AI Call Center API",
    description="Backend API for AI-powered call center with VOIP integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(outbound_router)
app.include_router(vocabulary_router)

# Mount static files for web testing interface
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the web testing interface"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "AI Call Center API", "docs": "/docs"}


@app.get("/vocabulary-manager")
async def vocabulary_manager():
    """Serve the vocabulary management interface"""
    vocab_path = static_dir / "vocabulary.html"
    if vocab_path.exists():
        return FileResponse(str(vocab_path))
    return {"message": "Vocabulary Manager", "api": "/vocabulary"}


db = Database()
manager = ConnectionManager()



# ===========================================
# Pydantic Models
# ===========================================
class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    
class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None
    
class ConversationCreate(BaseModel):
    caller_id: Optional[str] = None
    metadata: Optional[dict] = None

class SynthesizeRequest(BaseModel):
    text: str
    reference_audio: Optional[str] = None


# ===========================================
# REST Endpoints
# ===========================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/conversations", response_model=dict)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    await db.create_conversation(
        conversation_id=conversation_id,
        caller_id=data.caller_id,
        metadata=data.metadata
    )
    return {"conversation_id": conversation_id, "greeting": GREETING}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details with messages"""
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.get_messages(conversation_id)
    return {
        "conversation": conversation,
        "messages": messages
    }


@app.post("/conversations/{conversation_id}/end")
async def end_conversation(conversation_id: str):
    """End a conversation"""
    await db.end_conversation(conversation_id)
    return {"status": "ended"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response with audio"""
    # Save user message
    await db.add_message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message
    )
    
    # Get LLM response
    async with httpx.AsyncClient(timeout=60.0) as client:
        llm_response = await client.post(
            f"{LLM_URL}/chat",
            json={
                "conversation_id": request.conversation_id,
                "message": request.message
            }
        )
        llm_data = llm_response.json()
        ai_response = llm_data.get("response", "Lo siento, no pude procesar su solicitud.")
    
    # Generate TTS audio
    audio_url = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            tts_response = await client.post(
                f"{TTS_URL}/synthesize",
                json={"text": ai_response}
            )
            if tts_response.status_code == 200:
                audio_url = tts_response.json().get("audio_url")
    except Exception as e:
        print(f"TTS error: {e}")
    
    # Save assistant message
    await db.add_message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=ai_response,
        audio_path=audio_url
    )
    
    return ChatResponse(response=ai_response, audio_url=audio_url)


@app.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """Synthesize speech from text"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TTS_URL}/synthesize",
            json={"text": request.text, "reference_audio": request.reference_audio}
        )
        return response.json()


# ===========================================
# WebSocket Endpoints
# ===========================================
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time audio streaming
    
    Protocol:
    - Client sends audio chunks (binary)
    - Server responds with transcription and AI audio
    """
    await manager.connect(websocket, conversation_id)
    
    try:
        # Send greeting
        greeting_audio = await generate_greeting_audio()
        await websocket.send_json({
            "type": "greeting",
            "text": GREETING,
            "audio": greeting_audio
        })
        
        audio_buffer = bytearray()
        
        while True:
            # Receive audio data
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio chunk received
                audio_buffer.extend(data["bytes"])
                
                # Process when we have enough audio (e.g., 1 second)
                if len(audio_buffer) >= 16000 * 2:  # 16kHz, 16-bit
                    await process_audio_chunk(
                        websocket, 
                        conversation_id, 
                        bytes(audio_buffer)
                    )
                    audio_buffer.clear()
                    
            elif "text" in data:
                # Text command received
                message = data["text"]
                if message == "end_turn":
                    # Process remaining audio
                    if audio_buffer:
                        await process_audio_chunk(
                            websocket,
                            conversation_id,
                            bytes(audio_buffer)
                        )
                        audio_buffer.clear()
                        
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
        await db.end_conversation(conversation_id)


async def generate_greeting_audio() -> Optional[str]:
    """Generate audio for the greeting message"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TTS_URL}/synthesize",
                json={"text": GREETING}
            )
            if response.status_code == 200:
                return response.json().get("audio_base64")
    except Exception as e:
        print(f"Greeting audio error: {e}")
    return None


async def process_audio_chunk(
    websocket: WebSocket, 
    conversation_id: str, 
    audio_data: bytes
):
    """Process an audio chunk: STT -> LLM -> TTS"""
    try:
        # 1. Speech to Text
        async with httpx.AsyncClient(timeout=30.0) as client:
            stt_response = await client.post(
                f"{STT_URL}/transcribe",
                files={"audio": ("audio.wav", audio_data, "audio/wav")}
            )
            transcription = stt_response.json().get("text", "")
        
        if not transcription.strip():
            return
            
        # Send transcription to client
        await websocket.send_json({
            "type": "transcription",
            "text": transcription
        })
        
        # Save user message
        await db.add_message(conversation_id, "user", transcription)
        
        # 2. Get LLM response
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_response = await client.post(
                f"{LLM_URL}/chat",
                json={
                    "conversation_id": conversation_id,
                    "message": transcription
                }
            )
            ai_response = llm_response.json().get("response", "")
        
        # Send AI response text
        await websocket.send_json({
            "type": "response",
            "text": ai_response
        })
        
        # Save assistant message
        await db.add_message(conversation_id, "assistant", ai_response)
        
        # 3. Text to Speech
        async with httpx.AsyncClient(timeout=30.0) as client:
            tts_response = await client.post(
                f"{TTS_URL}/synthesize",
                json={"text": ai_response}
            )
            if tts_response.status_code == 200:
                audio_base64 = tts_response.json().get("audio_base64")
                await websocket.send_json({
                    "type": "audio",
                    "audio": audio_base64
                })
                
    except Exception as e:
        print(f"Audio processing error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


# ===========================================
# Asterisk AudioSocket Handler
# ===========================================
@app.websocket("/audiosocket/{conversation_id}")
async def audiosocket_handler(websocket: WebSocket, conversation_id: str):
    """
    AudioSocket handler for Asterisk integration
    Handles raw audio from Asterisk and processes through AI pipeline
    """
    await manager.connect(websocket, conversation_id)
    
    try:
        # Create conversation in database
        await db.create_conversation(conversation_id=conversation_id)
        
        # Send greeting
        greeting_audio = await generate_greeting_audio()
        if greeting_audio:
            await websocket.send_bytes(greeting_audio)
        
        audio_buffer = bytearray()
        silence_frames = 0
        SILENCE_THRESHOLD = 500  # Adjust based on audio format
        MAX_SILENCE_FRAMES = 30  # ~1.5 seconds of silence triggers processing
        
        while True:
            data = await websocket.receive_bytes()
            
            # Simple VAD: check if audio is silence
            audio_level = sum(abs(b - 128) for b in data) / len(data)
            
            if audio_level < SILENCE_THRESHOLD:
                silence_frames += 1
                if silence_frames >= MAX_SILENCE_FRAMES and audio_buffer:
                    # Process accumulated audio
                    response_audio = await process_and_respond(
                        conversation_id, 
                        bytes(audio_buffer)
                    )
                    if response_audio:
                        await websocket.send_bytes(response_audio)
                    audio_buffer.clear()
                    silence_frames = 0
            else:
                silence_frames = 0
                audio_buffer.extend(data)
                
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
        await db.end_conversation(conversation_id)


async def process_and_respond(conversation_id: str, audio_data: bytes) -> Optional[bytes]:
    """Process audio and return response audio bytes"""
    try:
        # STT
        async with httpx.AsyncClient(timeout=30.0) as client:
            stt_response = await client.post(
                f"{STT_URL}/transcribe",
                files={"audio": ("audio.wav", audio_data, "audio/wav")}
            )
            transcription = stt_response.json().get("text", "")
        
        if not transcription.strip():
            return None
            
        await db.add_message(conversation_id, "user", transcription)
        
        # LLM
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_response = await client.post(
                f"{LLM_URL}/chat",
                json={
                    "conversation_id": conversation_id,
                    "message": transcription
                }
            )
            ai_response = llm_response.json().get("response", "")
        
        await db.add_message(conversation_id, "assistant", ai_response)
        
        # TTS - get raw audio bytes
        async with httpx.AsyncClient(timeout=30.0) as client:
            tts_response = await client.post(
                f"{TTS_URL}/synthesize",
                json={"text": ai_response, "return_bytes": True}
            )
            if tts_response.status_code == 200:
                return tts_response.content
                
    except Exception as e:
        print(f"Process error: {e}")
    
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
