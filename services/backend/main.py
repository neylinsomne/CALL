"""
AI Call Center - Backend API
FastAPI application with WebSocket support for real-time voice processing
"""

import os
import uuid
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from database import Database, Conversation, Message
from websocket_manager import ConnectionManager
from outbound import router as outbound_router
from vocabulary import router as vocabulary_router
from webhooks import router as webhooks_router, trigger_webhook_event
from config_manager import router as config_router, init_config_manager
from adaptive_flow import initialize_adaptive_flow, get_current_flow
from license_validator import get_license_validator
from license_admin import router as license_admin_router
from admin_api import router as admin_api_router
from client_api import router as client_api_router
from auth import expire_old_tokens
from __version__ import __version__, __license_required__

# Configure loguru
logger.add(
    "logs/backend_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


# ===========================================
# Configuration
# ===========================================
TTS_URL = os.getenv("TTS_URL", "http://tts:8001")
STT_URL = os.getenv("STT_URL", "http://stt:8002")
LLM_URL = os.getenv("LLM_URL", "http://llm:8003")
AUDIO_PREPROCESS_URL = os.getenv("AUDIO_PREPROCESS_URL", "http://audio_preprocess:8004")
GREETING = os.getenv("CALL_CENTER_GREETING", "Hola, bienvenido. ¿En qué puedo ayudarle?")
ENABLE_DENOISE = os.getenv("ENABLE_DENOISE", "true").lower() == "true"


# ===========================================
# Lifespan
# ===========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    init_config_manager()  # Initialize configuration manager
    logger.info("✅ Configuration manager initialized")

    # Initialize license validator (if required)
    if __license_required__:
        try:
            license_validator = get_license_validator()
            await license_validator.start()
            logger.info("🔐 License validated successfully")
            logger.info(f"   Client: {license_validator.license_info.get('client_name')}")
            logger.info(f"   Max calls: {license_validator.max_concurrent_calls}")
            logger.info(f"   Expires: {license_validator.license_info.get('expires_at')}")
        except Exception as e:
            logger.error(f"❌ License validation failed: {e}")
            logger.error("   System will not accept calls without valid license")
            # Don't exit - allow system to start but reject calls
    else:
        logger.warning("⚠️  License validation disabled (development mode)")

    # Initialize adaptive flow
    await initialize_adaptive_flow()
    flow_info = get_current_flow().get_flow_info()
    logger.info(f"🔄 Adaptive flow ready: {flow_info['flow_type']}")

    # Start background token expiration task
    async def _token_expiry_loop():
        while True:
            try:
                await expire_old_tokens()
            except Exception as e:
                logger.error(f"Token expiration task error: {e}")
            await asyncio.sleep(3600)  # Check every hour

    token_task = asyncio.create_task(_token_expiry_loop())
    logger.info("Token expiration scheduler started (every 1h)")

    yield
    # Shutdown
    token_task.cancel()
    if __license_required__:
        try:
            license_validator = get_license_validator()
            await license_validator.stop()
        except Exception:
            pass
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
app.include_router(webhooks_router)
app.include_router(config_router)  # Configuration wizard endpoints
app.include_router(license_admin_router)  # License management endpoints (admin only)
app.include_router(admin_api_router)  # Multi-tenant admin API (orgs, tokens, agents)
app.include_router(client_api_router)  # Client API with scope-based permissions

try:
    from sentiment import router as sentiment_router
    app.include_router(sentiment_router)
except ImportError:
    logger.warning("Sentiment router not available")

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

# Shared HTTP client with retry capability
http_client = httpx.AsyncClient(timeout=60.0)

# Global state for interruption handling
conversation_playback_state = {}  # {conversation_id: {"is_speaking": bool, "task": asyncio.Task}}

# Global state for voice profiles (Target Speaker Extraction)
conversation_voice_profiles = {}  # {conversation_id: {"profile": tensor, "audio_buffer": bytes}}

# Import sentiment analysis function
try:
    from sentiment import analyze_call_sentiment
except ImportError:
    logger.warning("Sentiment analysis not available")
    def analyze_call_sentiment(*args, **kwargs):
        return {"overall_sentiment": {"score": 0, "label": "neutral"}}

# Target Speaker Extraction and Prosody Analysis (optional, improve quality)
ENABLE_TARGET_EXTRACTION = os.getenv("ENABLE_TARGET_EXTRACTION", "false").lower() == "true"
ENABLE_PROSODY_ANALYSIS = os.getenv("ENABLE_PROSODY_ANALYSIS", "true").lower() == "true"


# ===========================================
# License Validation Helper
# ===========================================
def check_license_call_limit() -> bool:
    """
    Verifica si se puede aceptar una nueva llamada según la licencia.

    Returns:
        True si se puede aceptar la llamada
    """
    if not __license_required__:
        return True

    try:
        license_validator = get_license_validator()
        if not license_validator.is_valid:
            logger.error("License is not valid - rejecting call")
            return False

        if not license_validator.can_accept_call():
            logger.warning(f"Call limit reached: {license_validator._active_calls}/{license_validator.max_concurrent_calls}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error checking license: {e}")
        return False

target_extractor = None
prosody_analyzer = None

if ENABLE_TARGET_EXTRACTION:
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "audio_preprocess"))
        from target_speaker import get_extractor
        target_extractor = get_extractor()
        logger.info("Target Speaker Extraction habilitado")
    except Exception as e:
        logger.warning(f"Target Speaker Extraction no disponible: {e}")
        ENABLE_TARGET_EXTRACTION = False

if ENABLE_PROSODY_ANALYSIS:
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "audio_preprocess"))
        from prosody_analyzer import get_prosody_analyzer
        prosody_analyzer = get_prosody_analyzer()
        logger.info("Prosody Analysis habilitado")
    except Exception as e:
        logger.warning(f"Prosody Analysis no disponible: {e}")
        ENABLE_PROSODY_ANALYSIS = False


# ===========================================
# Retry-enabled Service Calls
# ===========================================
@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.3, min=0.3, max=2),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True
)
async def call_denoise(audio_data: bytes) -> bytes:
    """Call audio preprocessing service for noise suppression"""
    logger.debug("Calling denoise service...")
    response = await http_client.post(
        f"{AUDIO_PREPROCESS_URL}/denoise_bytes",
        files={"audio": ("audio.wav", audio_data, "audio/wav")},
        timeout=10.0
    )
    response.raise_for_status()
    return response.content


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True
)
async def call_stt(audio_data: bytes, denoise: bool = True) -> str:
    """Call STT service with optional noise suppression"""
    # Apply noise suppression if enabled
    if ENABLE_DENOISE and denoise:
        try:
            audio_data = await call_denoise(audio_data)
            logger.debug("Audio denoised successfully")
        except Exception as e:
            logger.warning(f"Denoise failed, using original audio: {e}")
    
    logger.debug("Calling STT service...")
    response = await http_client.post(
        f"{STT_URL}/transcribe",
        files={"audio": ("audio.wav", audio_data, "audio/wav")},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json().get("text", "")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True
)
async def call_llm(conversation_id: str, message: str, use_tools: bool = False, context: Optional[str] = None) -> dict:
    """Call LLM service with retry logic and optional function calling"""
    logger.debug(f"Calling LLM for conversation {conversation_id}...")

    # Choose endpoint based on function calling
    endpoint = "/chat_with_tools" if use_tools else "/chat"

    # Prepare request payload
    payload = {
        "conversation_id": conversation_id,
        "message": message
    }

    # Add context if provided (for sentiment-aware responses)
    if context:
        payload["context"] = {"sentiment_guidance": context}

    response = await http_client.post(
        f"{LLM_URL}{endpoint}",
        json=payload,
        timeout=60.0
    )
    response.raise_for_status()
    result = response.json()

    # Return structured response
    return {
        "response": result.get("response", ""),
        "tool_calls": result.get("tool_calls", [])
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True
)
async def call_tts(text: str, return_bytes: bool = False) -> dict:
    """Call TTS service with retry logic"""
    logger.debug(f"Calling TTS for text: {text[:30]}...")
    response = await http_client.post(
        f"{TTS_URL}/synthesize",
        json={"text": text, "return_bytes": return_bytes},
        timeout=30.0
    )
    response.raise_for_status()
    if return_bytes:
        return {"content": response.content}
    return response.json()



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
    """Health check endpoint with license status"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__
    }

    if __license_required__:
        try:
            license_validator = get_license_validator()
            health_data["license"] = {
                "valid": license_validator.is_valid,
                "active_calls": license_validator._active_calls,
                "max_calls": license_validator.max_concurrent_calls,
                "expires_at": license_validator.license_info.get("expires_at") if license_validator.license_info else None
            }
        except Exception as e:
            health_data["license"] = {
                "valid": False,
                "error": str(e)
            }

    return health_data


@app.get("/license/status")
async def license_status():
    """Get detailed license status"""
    if not __license_required__:
        return {"license_required": False, "mode": "development"}

    try:
        license_validator = get_license_validator()
        return {
            "license_required": True,
            "valid": license_validator.is_valid,
            "active_calls": license_validator._active_calls,
            "max_concurrent_calls": license_validator.max_concurrent_calls,
            "max_agents": license_validator.max_agents,
            "license_info": license_validator.license_info,
            "hardware_id": license_validator.hardware_id[:16] + "..." if license_validator.hardware_id else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting license status: {str(e)}"
        )


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
    """End a conversation and trigger webhook"""
    await db.end_conversation(conversation_id)

    # Get final metrics
    metrics = await db.get_conversation_metrics(conversation_id)

    # Trigger webhook
    asyncio.create_task(trigger_webhook_event(
        "call_ended",
        conversation_id,
        {"metrics": metrics}
    ))

    return {"status": "ended", "metrics": metrics}


@app.get("/conversations/{conversation_id}/metrics")
async def get_conversation_metrics(conversation_id: str):
    """Get quality metrics for a conversation"""
    metrics = await db.get_conversation_metrics(conversation_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found for this conversation")
    return metrics


@app.get("/metrics/summary")
async def get_metrics_summary(limit: int = 100):
    """Get aggregated metrics across all recent conversations"""
    return await db.get_all_metrics(limit)


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
    WebSocket endpoint for real-time audio streaming with prosody analysis

    Protocol:
    - Client sends audio chunks (binary)
    - Server analyzes prosody (questions, pauses, emotion)
    - Server responds with transcription and AI audio
    """
    # Check license before accepting call
    if not check_license_call_limit():
        await websocket.close(code=1008, reason="License limit exceeded or invalid")
        logger.error(f"[{conversation_id}] Call rejected - license limit exceeded")
        return

    # Increment active calls counter
    if __license_required__:
        license_validator = get_license_validator()
        license_validator.increment_active_calls()
        logger.info(f"Active calls: {license_validator._active_calls}/{license_validator.max_concurrent_calls}")

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
        last_speech_time = datetime.utcnow()
        waiting_for_more = False

        # Initialize voice profile state
        if ENABLE_TARGET_EXTRACTION and conversation_id not in conversation_voice_profiles:
            conversation_voice_profiles[conversation_id] = {
                "profile": None,
                "audio_buffer": bytearray(),
                "profile_created": False
            }

        while True:
            # Receive audio data
            data = await websocket.receive()

            if "bytes" in data:
                # Audio chunk received
                audio_buffer.extend(data["bytes"])

                # Build voice profile from first 3 seconds
                if ENABLE_TARGET_EXTRACTION:
                    profile_state = conversation_voice_profiles.get(conversation_id)
                    if profile_state and not profile_state["profile_created"]:
                        profile_state["audio_buffer"].extend(data["bytes"])

                        # Create profile when we have 3 seconds
                        if len(profile_state["audio_buffer"]) >= 16000 * 2 * 3:  # 3 seconds
                            try:
                                profile = target_extractor.create_voice_profile(
                                    bytes(profile_state["audio_buffer"])
                                )
                                profile_state["profile"] = profile
                                profile_state["profile_created"] = True
                                logger.info(f"[{conversation_id}] Voice profile created")

                                await websocket.send_json({
                                    "type": "voice_profile_created",
                                    "message": "Perfil de voz creado exitosamente"
                                })
                            except Exception as e:
                                logger.error(f"Error creating voice profile: {e}")

                # Analyze prosody to decide when to process
                if ENABLE_PROSODY_ANALYSIS and len(audio_buffer) >= 16000 * 2:  # At least 1 second
                    prosody_data = prosody_analyzer.analyze_audio(bytes(audio_buffer))

                    # Send prosody info to client (for UI/debugging)
                    await websocket.send_json({
                        "type": "prosody",
                        "data": {
                            "is_question": prosody_data["is_question"],
                            "pause_duration": prosody_data["pause_duration"],
                            "should_wait": prosody_data["should_wait"],
                            "emotional_tone": prosody_data["emotional_tone"],
                            "has_speech": prosody_data["has_speech"]
                        }
                    })

                    # Decide if we should process now
                    if prosody_data["has_speech"]:
                        last_speech_time = datetime.utcnow()
                        waiting_for_more = prosody_data["should_wait"]

                    # Process if:
                    # 1. Not waiting for more speech
                    # 2. OR timeout (2.5 seconds since last speech)
                    time_since_speech = (datetime.utcnow() - last_speech_time).total_seconds()

                    if not waiting_for_more or time_since_speech > 2.5:
                        if prosody_data["has_speech"] or len(audio_buffer) >= 16000 * 4:  # 2 seconds minimum
                            await process_audio_chunk_with_context(
                                websocket,
                                conversation_id,
                                bytes(audio_buffer),
                                prosody_data
                            )
                            audio_buffer.clear()
                            waiting_for_more = False

                # Fallback: Process if buffer too large (prevent memory issues)
                elif len(audio_buffer) >= 16000 * 2 * 10:  # 10 seconds
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
                        prosody_data = None
                        if ENABLE_PROSODY_ANALYSIS:
                            prosody_data = prosody_analyzer.analyze_audio(bytes(audio_buffer))

                        await process_audio_chunk_with_context(
                            websocket,
                            conversation_id,
                            bytes(audio_buffer),
                            prosody_data
                        )
                        audio_buffer.clear()

    except WebSocketDisconnect:
        manager.disconnect(conversation_id)

        # Decrement active calls counter
        if __license_required__:
            try:
                license_validator = get_license_validator()
                license_validator.decrement_active_calls()
                logger.info(f"Call ended. Active calls: {license_validator._active_calls}/{license_validator.max_concurrent_calls}")
            except Exception as e:
                logger.error(f"Error decrementing call counter: {e}")

        # Clean up voice profile
        if conversation_id in conversation_voice_profiles:
            del conversation_voice_profiles[conversation_id]

        await db.end_conversation(conversation_id)


async def process_audio_chunk_streaming(
    websocket: WebSocket,
    conversation_id: str,
    audio_data: bytes
):
    """
    Process audio chunk with streaming LLM response for lower perceived latency.
    Synthesizes audio sentence by sentence as LLM generates text.
    """
    start_time = datetime.utcnow()
    metrics = {}

    try:
        # Check for interruptions
        if conversation_id in conversation_playback_state:
            state = conversation_playback_state[conversation_id]
            if state.get("is_speaking", False):
                logger.info(f"[{conversation_id}] Interruption detected!")
                if "task" in state and not state["task"].done():
                    state["task"].cancel()
                await websocket.send_json({"type": "interrupt"})
                state["is_speaking"] = False
                await db.log_event(conversation_id=conversation_id, event_type="interruption",
                                  details={"timestamp": datetime.utcnow().isoformat()})

        # 1. STT with metrics
        stt_start = datetime.utcnow()
        transcription = await call_stt(audio_data)
        metrics["stt_latency_ms"] = int((datetime.utcnow() - stt_start).total_seconds() * 1000)

        if not transcription.strip():
            return

        logger.info(f"[{conversation_id}] User: {transcription[:50]}...")
        await websocket.send_json({"type": "transcription", "text": transcription})
        await db.add_message(conversation_id, "user", transcription)

        # 2. Sentiment analysis
        sentiment = await analyze_sentiment(transcription)
        metrics["sentiment_score"] = sentiment["score"]
        metrics["sentiment_label"] = sentiment["label"]
        await websocket.send_json({"type": "sentiment", "sentiment": sentiment["label"], "score": sentiment["score"]})

        # 3. LLM Streaming
        llm_start = datetime.utcnow()
        full_response = ""
        sentence_buffer = ""
        audio_chunks_sent = 0

        try:
            # Call streaming endpoint
            async with http_client.stream(
                "POST",
                f"{LLM_URL}/chat/stream",
                json={
                    "conversation_id": conversation_id,
                    "message": transcription,
                    "context": {"sentiment_guidance": sentiment.get("guidance", "")}
                },
                timeout=60.0
            ) as stream:
                async for line in stream.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]  # Remove "data: " prefix

                        if chunk == "[DONE]":
                            break

                        if chunk.startswith("[ERROR]"):
                            logger.error(f"LLM streaming error: {chunk}")
                            break

                        full_response += chunk
                        sentence_buffer += chunk

                        # Check if we completed a sentence
                        if chunk in [".", "?", "!", ":", ";"]:
                            # Synthesize completed sentence immediately
                            if sentence_buffer.strip():
                                try:
                                    tts_result = await call_tts(sentence_buffer.strip())
                                    audio_base64 = tts_result.get("audio_base64")

                                    if audio_base64:
                                        await websocket.send_json({
                                            "type": "audio_chunk",
                                            "audio": audio_base64,
                                            "text": sentence_buffer.strip()
                                        })
                                        audio_chunks_sent += 1

                                        # Mark as speaking on first chunk
                                        if audio_chunks_sent == 1:
                                            if conversation_id not in conversation_playback_state:
                                                conversation_playback_state[conversation_id] = {}
                                            conversation_playback_state[conversation_id]["is_speaking"] = True

                                except Exception as tts_error:
                                    logger.error(f"TTS streaming error: {tts_error}")

                                sentence_buffer = ""

                # Process any remaining text
                if sentence_buffer.strip():
                    tts_result = await call_tts(sentence_buffer.strip())
                    audio_base64 = tts_result.get("audio_base64")
                    if audio_base64:
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "audio": audio_base64,
                            "text": sentence_buffer.strip()
                        })
                        audio_chunks_sent += 1

        except Exception as stream_error:
            logger.error(f"Streaming error: {stream_error}. Falling back to non-streaming.")
            # Fallback to regular processing
            llm_result = await call_llm(conversation_id, transcription, use_tools=False, context=sentiment.get("guidance"))
            full_response = llm_result["response"]

        metrics["llm_latency_ms"] = int((datetime.utcnow() - llm_start).total_seconds() * 1000)

        logger.info(f"[{conversation_id}] AI: {full_response[:50]}... ({audio_chunks_sent} chunks)")

        # Send complete response
        await websocket.send_json({"type": "response", "text": full_response})
        await db.add_message(conversation_id, "assistant", full_response)

        # Mark speaking done
        async def mark_speaking_done():
            await asyncio.sleep(len(full_response) * 0.05)
            if conversation_id in conversation_playback_state:
                conversation_playback_state[conversation_id]["is_speaking"] = False

        task = asyncio.create_task(mark_speaking_done())
        if conversation_id in conversation_playback_state:
            conversation_playback_state[conversation_id]["task"] = task

        # Log metrics
        metrics["total_latency_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        metrics["streaming_chunks"] = audio_chunks_sent
        await db.log_event(conversation_id=conversation_id, event_type="turn_completed_streaming", details=metrics)

        logger.info(f"[{conversation_id}] Streaming metrics: STT={metrics['stt_latency_ms']}ms, "
                   f"Total={metrics['total_latency_ms']}ms, Chunks={audio_chunks_sent}")

    except Exception as e:
        logger.error(f"[{conversation_id}] Streaming processing error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


async def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of a message"""
    try:
        # Simple keyword-based sentiment analysis
        text_lower = text.lower()

        # Frustration indicators
        frustrated_keywords = ["no funciona", "problema", "mal", "molesto", "frustrado", "cansado", "harto"]
        # Confusion indicators
        confused_keywords = ["no entiendo", "qué", "cómo", "confundido", "explicar", "duda"]
        # Positive indicators
        positive_keywords = ["gracias", "perfecto", "excelente", "bien", "contento", "feliz"]

        frustration_score = sum(1 for k in frustrated_keywords if k in text_lower)
        confusion_score = sum(1 for k in confused_keywords if k in text_lower)
        positive_score = sum(1 for k in positive_keywords if k in text_lower)

        if frustration_score >= 2:
            return {"label": "frustrated", "score": -0.7, "guidance": "El cliente parece frustrado. Sé más empático y ofrece transferencia a un agente humano."}
        elif confusion_score >= 2:
            return {"label": "confused", "score": -0.3, "guidance": "El cliente no entiende. Simplifica tu respuesta y usa lenguaje más claro."}
        elif positive_score >= 1:
            return {"label": "positive", "score": 0.8, "guidance": "El cliente está satisfecho. Mantén el tono positivo."}
        else:
            return {"label": "neutral", "score": 0.0, "guidance": ""}

    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return {"label": "neutral", "score": 0.0, "guidance": ""}


async def execute_tool_call(tool_name: str, arguments: dict, conversation_id: str) -> dict:
    """Execute a function/tool call from the LLM"""
    try:
        if tool_name == "transfer_to_agent":
            department = arguments.get("department", "general")
            priority = arguments.get("priority", "normal")
            logger.info(f"[{conversation_id}] Transfer requested to {department} with priority {priority}")

            # Log the transfer event
            await db.log_event(
                conversation_id=conversation_id,
                event_type="transfer_requested",
                details={"department": department, "priority": priority}
            )

            return {
                "success": True,
                "message": f"Transferencia iniciada al departamento de {department}.",
                "action": "transfer"
            }

        elif tool_name == "schedule_callback":
            phone = arguments.get("phone")
            datetime_str = arguments.get("datetime")
            reason = arguments.get("reason", "")

            logger.info(f"[{conversation_id}] Callback scheduled for {phone} at {datetime_str}")

            await db.log_event(
                conversation_id=conversation_id,
                event_type="callback_scheduled",
                details={"phone": phone, "datetime": datetime_str, "reason": reason}
            )

            return {
                "success": True,
                "message": f"Llamada programada para {datetime_str}.",
                "action": "callback_scheduled"
            }

        elif tool_name == "lookup_customer":
            customer_id = arguments.get("customer_id")
            logger.info(f"[{conversation_id}] Customer lookup: {customer_id}")

            # Mock customer data - in production, query real database
            return {
                "success": True,
                "data": {
                    "customer_id": customer_id,
                    "name": "Cliente Demo",
                    "status": "active",
                    "last_contact": "2024-01-15"
                }
            }

        else:
            return {"success": False, "message": f"Tool {tool_name} not implemented"}

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"success": False, "message": str(e)}


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
    """Process an audio chunk: STT -> LLM -> TTS with retry logic, sentiment analysis, and interruption handling"""
    start_time = datetime.utcnow()
    metrics = {}

    try:
        # Check if assistant is currently speaking (interruption detection)
        if conversation_id in conversation_playback_state:
            state = conversation_playback_state[conversation_id]
            if state.get("is_speaking", False):
                # User interrupted the assistant
                logger.info(f"[{conversation_id}] Interruption detected!")

                # Cancel current playback
                if "task" in state and not state["task"].done():
                    state["task"].cancel()

                # Send interruption signal
                await websocket.send_json({"type": "interrupt"})

                # Mark as not speaking
                state["is_speaking"] = False

                # Log interruption event
                await db.log_event(
                    conversation_id=conversation_id,
                    event_type="interruption",
                    details={"timestamp": datetime.utcnow().isoformat()}
                )

        # 1. Speech to Text (with retry and metrics)
        stt_start = datetime.utcnow()
        transcription = await call_stt(audio_data)
        stt_end = datetime.utcnow()
        metrics["stt_latency_ms"] = int((stt_end - stt_start).total_seconds() * 1000)

        if not transcription.strip():
            return

        logger.info(f"[{conversation_id}] User: {transcription[:50]}...")

        # Send transcription to client
        await websocket.send_json({
            "type": "transcription",
            "text": transcription
        })

        # Save user message
        await db.add_message(conversation_id, "user", transcription)

        # 2. Sentiment Analysis
        sentiment_start = datetime.utcnow()
        sentiment = await analyze_sentiment(transcription)
        sentiment_end = datetime.utcnow()
        metrics["sentiment_score"] = sentiment["score"]
        metrics["sentiment_label"] = sentiment["label"]

        # Send sentiment to client (optional, for real-time dashboard)
        await websocket.send_json({
            "type": "sentiment",
            "sentiment": sentiment["label"],
            "score": sentiment["score"]
        })

        logger.info(f"[{conversation_id}] Sentiment: {sentiment['label']} ({sentiment['score']})")

        # Trigger webhook if sentiment is negative
        if sentiment["label"] in ["frustrated", "angry"] or sentiment["score"] < -0.5:
            asyncio.create_task(trigger_webhook_event(
                "sentiment_alert",
                conversation_id,
                {"sentiment": sentiment["label"], "score": sentiment["score"], "message": transcription}
            ))

        # 3. Get LLM response with context (with retry and metrics)
        llm_start = datetime.utcnow()
        use_tools = True  # Enable function calling
        llm_result = await call_llm(
            conversation_id,
            transcription,
            use_tools=use_tools,
            context=sentiment.get("guidance")
        )
        llm_end = datetime.utcnow()
        metrics["llm_latency_ms"] = int((llm_end - llm_start).total_seconds() * 1000)

        ai_response = llm_result["response"]
        tool_calls = llm_result.get("tool_calls", [])

        # 4. Execute tool calls if any
        if tool_calls:
            logger.info(f"[{conversation_id}] Executing {len(tool_calls)} tool calls")
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})

                tool_result = await execute_tool_call(tool_name, arguments, conversation_id)

                # Send tool execution result to client
                await websocket.send_json({
                    "type": "tool_call",
                    "tool": tool_name,
                    "result": tool_result
                })

        logger.info(f"[{conversation_id}] AI: {ai_response[:50]}...")

        # Send AI response text
        await websocket.send_json({
            "type": "response",
            "text": ai_response
        })

        # Save assistant message
        await db.add_message(conversation_id, "assistant", ai_response)

        # 5. Text to Speech (with retry and metrics)
        tts_start = datetime.utcnow()
        tts_result = await call_tts(ai_response)
        tts_end = datetime.utcnow()
        metrics["tts_latency_ms"] = int((tts_end - tts_start).total_seconds() * 1000)

        audio_base64 = tts_result.get("audio_base64")
        if audio_base64:
            # Mark assistant as speaking
            if conversation_id not in conversation_playback_state:
                conversation_playback_state[conversation_id] = {}
            conversation_playback_state[conversation_id]["is_speaking"] = True

            # Send audio
            await websocket.send_json({
                "type": "audio",
                "audio": audio_base64
            })

            # Create a task that marks speaking as done after audio duration
            async def mark_speaking_done():
                # Estimate audio duration (assuming 16kHz, 16-bit)
                # In production, get actual duration from TTS service
                await asyncio.sleep(len(ai_response) * 0.05)  # Rough estimate: 50ms per character
                if conversation_id in conversation_playback_state:
                    conversation_playback_state[conversation_id]["is_speaking"] = False

            task = asyncio.create_task(mark_speaking_done())
            conversation_playback_state[conversation_id]["task"] = task

        # 6. Calculate total latency and log metrics
        end_time = datetime.utcnow()
        metrics["total_latency_ms"] = int((end_time - start_time).total_seconds() * 1000)

        # Log metrics to database
        await db.log_event(
            conversation_id=conversation_id,
            event_type="turn_completed",
            details=metrics
        )

        logger.info(f"[{conversation_id}] Metrics: STT={metrics['stt_latency_ms']}ms, "
                   f"LLM={metrics['llm_latency_ms']}ms, TTS={metrics['tts_latency_ms']}ms, "
                   f"Total={metrics['total_latency_ms']}ms")

        # Trigger webhook for turn completed
        asyncio.create_task(trigger_webhook_event(
            "turn_completed",
            conversation_id,
            {
                "metrics": metrics,
                "user_message": transcription[:100],
                "ai_response": ai_response[:100]
            }
        ))

    except Exception as e:
        logger.error(f"[{conversation_id}] Audio processing error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


async def process_audio_chunk_with_context(
    websocket: WebSocket,
    conversation_id: str,
    audio_data: bytes,
    prosody_data: Optional[Dict] = None
):
    """
    Process audio chunk with prosody context and target speaker extraction.
    Handles questions, pauses, and emotional tone.
    """
    start_time = datetime.utcnow()
    metrics = {}

    try:
        # Check for interruptions
        if conversation_id in conversation_playback_state:
            state = conversation_playback_state[conversation_id]
            if state.get("is_speaking", False):
                logger.info(f"[{conversation_id}] Interruption detected!")
                if "task" in state and not state["task"].done():
                    state["task"].cancel()
                await websocket.send_json({"type": "interrupt"})
                state["is_speaking"] = False
                await db.log_event(conversation_id=conversation_id, event_type="interruption",
                                  details={"timestamp": datetime.utcnow().isoformat()})

        # 0. Target Speaker Extraction (if enabled and profile exists)
        if ENABLE_TARGET_EXTRACTION:
            profile_state = conversation_voice_profiles.get(conversation_id)
            if profile_state and profile_state.get("profile") is not None:
                try:
                    extraction_start = datetime.utcnow()
                    audio_data = target_extractor.extract_target_speaker(
                        audio_data,
                        profile_state["profile"],
                        similarity_threshold=0.5
                    )
                    extraction_time = (datetime.utcnow() - extraction_start).total_seconds() * 1000
                    metrics["target_extraction_ms"] = int(extraction_time)
                    logger.debug(f"[{conversation_id}] Target extraction: {extraction_time:.0f}ms")
                except Exception as e:
                    logger.error(f"Target extraction error: {e}")

        # 1. Speech to Text (with retry and metrics)
        stt_start = datetime.utcnow()
        transcription = await call_stt(audio_data)
        stt_end = datetime.utcnow()
        metrics["stt_latency_ms"] = int((stt_end - stt_start).total_seconds() * 1000)

        if not transcription.strip():
            return

        logger.info(f"[{conversation_id}] User: {transcription[:50]}...")

        # Add prosody information to transcription display
        transcription_data = {"type": "transcription", "text": transcription}
        if prosody_data:
            transcription_data["prosody"] = {
                "is_question": prosody_data.get("is_question", False),
                "emotional_tone": prosody_data.get("emotional_tone", "neutral"),
                "speech_rate": prosody_data.get("speech_rate", 0)
            }

        await websocket.send_json(transcription_data)

        # Save user message
        await db.add_message(conversation_id, "user", transcription)

        # 2. Sentiment Analysis
        sentiment_start = datetime.utcnow()
        sentiment = await analyze_sentiment(transcription)
        sentiment_end = datetime.utcnow()
        metrics["sentiment_score"] = sentiment["score"]
        metrics["sentiment_label"] = sentiment["label"]

        # Combine prosody and sentiment for richer context
        if prosody_data:
            metrics["prosody_is_question"] = prosody_data.get("is_question", False)
            metrics["prosody_emotional_tone"] = prosody_data.get("emotional_tone", "neutral")

            # If prosody detects frustration but sentiment doesn't, trust prosody
            if prosody_data.get("emotional_tone") in ["nervous", "concerned"] and sentiment["label"] == "neutral":
                sentiment["label"] = "frustrated"
                sentiment["score"] = -0.4

        # Send sentiment to client
        await websocket.send_json({
            "type": "sentiment",
            "sentiment": sentiment["label"],
            "score": sentiment["score"]
        })

        logger.info(f"[{conversation_id}] Sentiment: {sentiment['label']} ({sentiment['score']})")

        # Trigger webhook if sentiment is negative
        if sentiment["label"] in ["frustrated", "angry"] or sentiment["score"] < -0.5:
            asyncio.create_task(trigger_webhook_event(
                "sentiment_alert",
                conversation_id,
                {"sentiment": sentiment["label"], "score": sentiment["score"], "message": transcription}
            ))

        # 3. Build LLM context with prosody information
        llm_context = sentiment.get("guidance", "")

        # Add prosody-based guidance
        if prosody_data:
            if prosody_data.get("is_question"):
                llm_context += " El usuario hizo una pregunta. Asegúrate de responder directamente."

            emotional_tone = prosody_data.get("emotional_tone", "neutral")
            if emotional_tone == "nervous":
                llm_context += " El usuario parece nervioso. Responde con calma y claridad."
            elif emotional_tone == "concerned":
                llm_context += " El usuario está preocupado. Muestra empatía y ofrece soluciones concretas."
            elif emotional_tone == "excited":
                llm_context += " El usuario está entusiasmado. Mantén un tono positivo."

        # 4. Get LLM response with context (with retry and metrics)
        llm_start = datetime.utcnow()
        use_tools = True  # Enable function calling
        llm_result = await call_llm(
            conversation_id,
            transcription,
            use_tools=use_tools,
            context=llm_context if llm_context else None
        )
        llm_end = datetime.utcnow()
        metrics["llm_latency_ms"] = int((llm_end - llm_start).total_seconds() * 1000)

        ai_response = llm_result["response"]
        tool_calls = llm_result.get("tool_calls", [])

        # 5. Execute tool calls if any
        if tool_calls:
            logger.info(f"[{conversation_id}] Executing {len(tool_calls)} tool calls")
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})

                tool_result = await execute_tool_call(tool_name, arguments, conversation_id)

                # Send tool execution result to client
                await websocket.send_json({
                    "type": "tool_call",
                    "tool": tool_name,
                    "result": tool_result
                })

        logger.info(f"[{conversation_id}] AI: {ai_response[:50]}...")

        # Send AI response text
        await websocket.send_json({
            "type": "response",
            "text": ai_response
        })

        # Save assistant message
        await db.add_message(conversation_id, "assistant", ai_response)

        # 6. Text to Speech (with retry and metrics)
        tts_start = datetime.utcnow()
        tts_result = await call_tts(ai_response)
        tts_end = datetime.utcnow()
        metrics["tts_latency_ms"] = int((tts_end - tts_start).total_seconds() * 1000)

        audio_base64 = tts_result.get("audio_base64")
        if audio_base64:
            # Mark assistant as speaking
            if conversation_id not in conversation_playback_state:
                conversation_playback_state[conversation_id] = {}
            conversation_playback_state[conversation_id]["is_speaking"] = True

            # Send audio
            await websocket.send_json({
                "type": "audio",
                "audio": audio_base64
            })

            # Create a task that marks speaking as done after audio duration
            async def mark_speaking_done():
                await asyncio.sleep(len(ai_response) * 0.05)  # Rough estimate
                if conversation_id in conversation_playback_state:
                    conversation_playback_state[conversation_id]["is_speaking"] = False

            task = asyncio.create_task(mark_speaking_done())
            conversation_playback_state[conversation_id]["task"] = task

        # 7. Calculate total latency and log metrics
        end_time = datetime.utcnow()
        metrics["total_latency_ms"] = int((end_time - start_time).total_seconds() * 1000)

        # Log metrics to database
        await db.log_event(
            conversation_id=conversation_id,
            event_type="turn_completed_with_context",
            details=metrics
        )

        logger.info(f"[{conversation_id}] Metrics: STT={metrics['stt_latency_ms']}ms, "
                   f"LLM={metrics['llm_latency_ms']}ms, TTS={metrics['tts_latency_ms']}ms, "
                   f"Total={metrics['total_latency_ms']}ms")

        # Trigger webhook for turn completed
        asyncio.create_task(trigger_webhook_event(
            "turn_completed",
            conversation_id,
            {
                "metrics": metrics,
                "user_message": transcription[:100],
                "ai_response": ai_response[:100],
                "prosody": prosody_data if prosody_data else {}
            }
        ))

    except Exception as e:
        logger.error(f"[{conversation_id}] Audio processing with context error: {e}")
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
    # Check license before accepting call
    if not check_license_call_limit():
        await websocket.close(code=1008, reason="License limit exceeded or invalid")
        logger.error(f"[Asterisk:{conversation_id}] Call rejected - license limit exceeded")
        return

    # Increment active calls counter
    if __license_required__:
        license_validator = get_license_validator()
        license_validator.increment_active_calls()
        logger.info(f"[Asterisk] Active calls: {license_validator._active_calls}/{license_validator.max_concurrent_calls}")

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

        # Decrement active calls counter
        if __license_required__:
            try:
                license_validator = get_license_validator()
                license_validator.decrement_active_calls()
                logger.info(f"[Asterisk] Call ended. Active calls: {license_validator._active_calls}/{license_validator.max_concurrent_calls}")
            except Exception as e:
                logger.error(f"Error decrementing call counter: {e}")

        await db.end_conversation(conversation_id)


async def process_and_respond(conversation_id: str, audio_data: bytes) -> Optional[bytes]:
    """Process audio and return response audio bytes with retry logic"""
    try:
        # STT (with retry)
        transcription = await call_stt(audio_data)
        
        if not transcription.strip():
            return None
        
        logger.info(f"[Asterisk:{conversation_id}] User: {transcription[:50]}...")
        await db.add_message(conversation_id, "user", transcription)
        
        # LLM (with retry)
        ai_response = await call_llm(conversation_id, transcription)
        
        logger.info(f"[Asterisk:{conversation_id}] AI: {ai_response[:50]}...")
        await db.add_message(conversation_id, "assistant", ai_response)
        
        # TTS - get raw audio bytes (with retry)
        tts_result = await call_tts(ai_response, return_bytes=True)
        return tts_result.get("content")
                
    except Exception as e:
        logger.error(f"[Asterisk:{conversation_id}] Process error: {e}")
    
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
