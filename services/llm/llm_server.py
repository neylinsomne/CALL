"""
LLM Service
LangChain integration with LM Studio for conversational AI
"""

import os
from typing import Optional, List, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage


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
    Process a chat message and return AI response
    """
    try:
        llm = get_llm()
        
        # Build messages
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Add conversation history
        history = get_conversation_history(request.conversation_id)
        for msg in history[-10:]:  # Last 10 messages for context
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
        
        return ChatResponse(
            response=ai_response,
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_with_tools")
async def chat_with_tools(request: ChatRequest):
    """
    Chat with tool/function calling capability
    For database lookups, appointment scheduling, etc.
    """
    try:
        llm = get_llm()
        
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
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        history = get_conversation_history(request.conversation_id)
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
        
        return {
            "response": ai_response,
            "conversation_id": request.conversation_id,
            "tool_calls": []  # Populate if model returns tool calls
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
