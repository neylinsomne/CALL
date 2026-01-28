"""
LLM Service
LangChain integration with LM Studio for conversational AI
"""

import os
import asyncio
from typing import Optional, List, Dict, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from loguru import logger

# Configure loguru
logger.add(
    "logs/llm_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


# ===========================================
# Configuration
# ===========================================
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")

# Call center system prompt
SYSTEM_PROMPT = """Eres un asistente de atención al cliente profesional y amable para un call center.

INSTRUCCIONES:
1. Responde siempre en español de manera clara y concisa
2. Sé cortés y empático con el cliente
3. Si el cliente tiene una consulta técnica, guíalo paso a paso
4. Si no puedes resolver el problema, ofrece transferir a un agente humano
5. Mantén las respuestas breves (máximo 2-3 oraciones) para que sean naturales en una llamada telefónica
6. No uses emojis ni formato especial, solo texto plano

INFORMACIÓN DEL SERVICIO:
- Horario de atención: Lunes a Viernes, 8:00 AM - 6:00 PM
- Para emergencias, el cliente puede marcar la extensión 911
- Los tiempos de respuesta típicos son de 24-48 horas para solicitudes

Responde de manera natural como si estuvieras hablando por teléfono."""


# ===========================================
# App Initialization
# ===========================================
app = FastAPI(
    title="LLM Service",
    description="LangChain-powered conversational AI for call center",
    version="1.0.0"
)


# ===========================================
# Conversation Memory Store
# ===========================================
conversation_memories: Dict[str, List[Dict]] = {}


def get_conversation_history(conversation_id: str) -> List[Dict]:
    """Get or create conversation history"""
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = []
    return conversation_memories[conversation_id]


def add_to_history(conversation_id: str, role: str, content: str):
    """Add message to conversation history"""
    history = get_conversation_history(conversation_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    # Keep last 20 messages for context window
    if len(history) > 20:
        conversation_memories[conversation_id] = history[-20:]


# ===========================================
# LLM Client
# ===========================================
def get_llm():
    """Get LangChain LLM client configured for LM Studio"""
    return ChatOpenAI(
        base_url=LM_STUDIO_URL,
        api_key="not-needed",  # LM Studio doesn't require API key
        model=LM_STUDIO_MODEL,
        temperature=0.7,
        max_tokens=256,  # Keep responses short for voice
    )


# ===========================================
# Pydantic Models
# ===========================================
class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    context_analysis: Optional[dict] = None


# ===========================================
# Context Analysis
# ===========================================
def analyze_conversation_context(history: List[Dict], current_message: str) -> Dict:
    """
    Analyze conversation flow to detect issues:
    - Repeated questions (user doesn't understand)
    - Topic changes
    - Escalation needs
    """
    analysis = {
        "needs_escalation": False,
        "confidence_level": 1.0,
        "suggested_action": None,
        "issues": []
    }

    if len(history) < 4:
        return analysis

    # Get last 5 user messages
    user_messages = [msg["content"].lower() for msg in history[-10:] if msg["role"] == "user"]
    current_lower = current_message.lower()

    # 1. Detect repetition (user asking same thing multiple times)
    repetition_count = 0
    for prev_msg in user_messages:
        # Check similarity (simple word overlap)
        prev_words = set(prev_msg.split())
        curr_words = set(current_lower.split())
        overlap = len(prev_words & curr_words) / max(len(curr_words), 1)
        if overlap > 0.6:  # 60% word overlap
            repetition_count += 1

    if repetition_count >= 2:
        analysis["issues"].append("repeated_question")
        analysis["needs_escalation"] = True
        analysis["suggested_action"] = "transfer_to_agent"
        analysis["confidence_level"] = 0.4

    # 2. Detect frustration keywords in history
    frustration_keywords = ["no funciona", "problema", "mal", "otra vez", "ya dije", "no entiende"]
    frustration_count = sum(1 for msg in user_messages[-3:] for kw in frustration_keywords if kw in msg)

    if frustration_count >= 2:
        analysis["issues"].append("user_frustrated")
        analysis["needs_escalation"] = True
        analysis["suggested_action"] = "transfer_to_agent"
        analysis["confidence_level"] = 0.3

    # 3. Detect explicit escalation requests
    escalation_keywords = ["hablar con", "agente", "humano", "persona", "supervisor", "gerente"]
    if any(kw in current_lower for kw in escalation_keywords):
        analysis["issues"].append("explicit_escalation_request")
        analysis["needs_escalation"] = True
        analysis["suggested_action"] = "transfer_to_agent"
        analysis["confidence_level"] = 0.2

    # 4. Detect confusion (many questions in a row)
    question_keywords = ["qué", "cómo", "cuál", "dónde", "por qué", "cuándo"]
    recent_questions = sum(1 for msg in user_messages[-4:] if any(kw in msg for kw in question_keywords))

    if recent_questions >= 3:
        analysis["issues"].append("user_confused")
        analysis["confidence_level"] = max(0.5, analysis["confidence_level"])

    return analysis


# ===========================================
# Endpoints
# ===========================================
@app.get("/health")
async def health():
    """Health check"""
    try:
        llm = get_llm()
        # Quick test
        return {
            "status": "healthy",
            "lm_studio_url": LM_STUDIO_URL,
            "model": LM_STUDIO_MODEL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response with context awareness
    """
    try:
        llm = get_llm()

        # Get conversation history
        history = get_conversation_history(request.conversation_id)

        # Analyze conversation context
        context_analysis = analyze_conversation_context(history, request.message)

        # Build system prompt with context guidance
        system_prompt = SYSTEM_PROMPT

        # Add sentiment guidance if provided
        if request.context and "sentiment_guidance" in request.context:
            sentiment_guidance = request.context["sentiment_guidance"]
            if sentiment_guidance:
                system_prompt += f"\n\nGUIDANCE: {sentiment_guidance}"

        # Add context-aware guidance
        if context_analysis["needs_escalation"]:
            system_prompt += "\n\nIMPORTANT: El cliente necesita asistencia especializada. Ofrece transferir la llamada a un agente humano de manera proactiva y empática."

        if "user_confused" in context_analysis["issues"]:
            system_prompt += "\n\nIMPORTANT: El cliente parece confundido. Simplifica tu respuesta al máximo y ofrece explicaciones paso a paso."

        # Build messages
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history (last 10 messages)
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Add current message
        messages.append(HumanMessage(content=request.message))

        # Get response
        response = llm.invoke(messages)
        ai_response = response.content

        # Clean up response for voice
        ai_response = clean_for_voice(ai_response)

        # Save to history
        add_to_history(request.conversation_id, "user", request.message)
        add_to_history(request.conversation_id, "assistant", ai_response)

        # Return response with context analysis
        return ChatResponse(
            response=ai_response,
            conversation_id=request.conversation_id,
            context_analysis=context_analysis  # Add to response model
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response token by token using SSE
    Reduces perceived latency by sending tokens as they're generated
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            llm = get_llm()
            
            # Build messages
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            
            # Add conversation history
            history = get_conversation_history(request.conversation_id)
            for msg in history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current message
            messages.append(HumanMessage(content=request.message))
            
            logger.info(f"Streaming response for conversation {request.conversation_id}")
            
            # Stream tokens
            full_response = ""
            async for chunk in llm.astream(messages):
                token = chunk.content
                full_response += token
                yield f"data: {token}\n\n"
            
            # Clean and save to history
            cleaned = clean_for_voice(full_response)
            add_to_history(request.conversation_id, "user", request.message)
            add_to_history(request.conversation_id, "assistant", cleaned)
            
            yield "data: [DONE]\n\n"
            logger.info(f"Completed streaming for {request.conversation_id}")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.post("/chat_with_tools")
async def chat_with_tools(request: ChatRequest):
    """
    Chat with tool/function calling capability
    For database lookups, appointment scheduling, etc.
    """
    try:
        llm = get_llm()

        # Get conversation history
        history = get_conversation_history(request.conversation_id)

        # Analyze conversation context
        context_analysis = analyze_conversation_context(history, request.message)

        # Build system prompt with context guidance
        system_prompt = SYSTEM_PROMPT

        # Add sentiment guidance if provided
        if request.context and "sentiment_guidance" in request.context:
            sentiment_guidance = request.context["sentiment_guidance"]
            if sentiment_guidance:
                system_prompt += f"\n\nGUIDANCE: {sentiment_guidance}"

        # If escalation is needed, automatically suggest transfer
        if context_analysis["needs_escalation"]:
            system_prompt += "\n\nIMPORTANT: Usa la función 'transfer_to_agent' proactivamente para ofrecer transferencia a un agente humano."

        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_customer",
                    "description": "Buscar información del cliente en la base de datos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID del cliente"
                            }
                        },
                        "required": ["customer_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_callback",
                    "description": "Programar llamada de seguimiento",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone": {"type": "string"},
                            "datetime": {"type": "string"},
                            "reason": {"type": "string"}
                        },
                        "required": ["phone", "datetime"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transfer_to_agent",
                    "description": "Transferir llamada a agente humano",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department": {"type": "string"},
                            "priority": {"type": "string"}
                        },
                        "required": ["department"]
                    }
                }
            }
        ]

        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=request.message))

        # Get response (note: tool calling depends on model support)
        response = llm.invoke(messages)
        ai_response = clean_for_voice(response.content)

        add_to_history(request.conversation_id, "user", request.message)
        add_to_history(request.conversation_id, "assistant", ai_response)

        # Check if model returned tool calls (if supported)
        tool_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = [
                {
                    "name": tc.get("name"),
                    "arguments": tc.get("args", {})
                }
                for tc in response.tool_calls
            ]

        return {
            "response": ai_response,
            "conversation_id": request.conversation_id,
            "tool_calls": tool_calls,
            "context_analysis": context_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{conversation_id}/history")
async def get_history(conversation_id: str):
    """Get conversation history"""
    return {
        "conversation_id": conversation_id,
        "messages": get_conversation_history(conversation_id)
    }


@app.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if conversation_id in conversation_memories:
        del conversation_memories[conversation_id]
    return {"status": "cleared"}


@app.post("/update_system_prompt")
async def update_prompt(prompt: str):
    """Update the system prompt (for customization)"""
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = prompt
    return {"status": "updated"}


# ===========================================
# Utilities
# ===========================================
def clean_for_voice(text: str) -> str:
    """Clean text for TTS output"""
    # Remove markdown formatting
    text = text.replace("**", "").replace("*", "")
    text = text.replace("```", "").replace("`", "")
    
    # Remove bullet points
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("-") or line.startswith("•"):
            line = line[1:].strip()
        if line.startswith("*"):
            line = line[1:].strip()
        if line:
            cleaned_lines.append(line)
    
    text = " ".join(cleaned_lines)
    
    # Remove multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    return text.strip()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
