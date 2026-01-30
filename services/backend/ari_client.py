"""
Asterisk REST Interface (ARI) Client
====================================

Cliente ARI para control programático de llamadas en tiempo real.

Funcionalidades:
- Eventos WebSocket en tiempo real (llamadas entrantes, hangup, DTMF, etc.)
- Control programático de llamadas (originar, transferir, colgar)
- Bridges dinámicos (conectar/desconectar llamadas)
- Grabación selectiva
- Integración con dashboard React vía WebSocket

Uso:
    from ari_client import ARIClient

    client = ARIClient()
    await client.connect()
    await client.run()
"""

import asyncio
import os
import logging
from typing import Dict, Optional, Callable
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ARIClient:
    """Cliente ARI asíncrono para Asterisk"""

    def __init__(
        self,
        host: str = None,
        port: int = 8088,
        username: str = "callcenter-ai",
        password: str = None,
        app_name: str = "callcenter-ai"
    ):
        """
        Inicializa el cliente ARI

        Args:
            host: Hostname de Asterisk (default: desde env ASTERISK_HOST)
            port: Puerto HTTP de Asterisk (default: 8088)
            username: Usuario ARI (default: callcenter-ai)
            password: Password ARI (default: desde env ARI_PASSWORD)
            app_name: Nombre de la aplicación Stasis
        """
        self.host = host or os.getenv("ASTERISK_HOST", "asterisk")
        self.port = port
        self.username = username
        self.password = password or os.getenv("ARI_PASSWORD", "ari123")
        self.app_name = app_name

        self.base_url = f"http://{self.host}:{self.port}/ari"
        self.ws_url = f"ws://{self.host}:{self.port}/ari/events"

        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None

        # Event handlers
        self.event_handlers: Dict[str, list[Callable]] = {}

        # Active channels tracking
        self.active_channels: Dict[str, dict] = {}

        logger.info(f"ARI Client initialized for {self.host}:{self.port}")

    async def connect(self):
        """Conecta al servidor ARI"""
        self.session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.username, self.password)
        )
        logger.info("ARI session created")

    async def disconnect(self):
        """Desconecta del servidor ARI"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        logger.info("ARI disconnected")

    # ============================================
    # EVENT HANDLING
    # ============================================

    def on(self, event_type: str, handler: Callable):
        """
        Registra un handler para un tipo de evento

        Args:
            event_type: Tipo de evento (ej: 'StasisStart', 'ChannelHangup')
            handler: Función async que recibe (event, channel)

        Example:
            @client.on('StasisStart')
            async def on_call_start(event, channel):
                print(f"Nueva llamada de {channel['caller']['number']}")
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Handler registered for {event_type}")

    async def _handle_event(self, event: dict):
        """Procesa un evento recibido desde WebSocket"""
        event_type = event.get("type")

        if not event_type:
            return

        logger.debug(f"Event received: {event_type}")

        # Actualizar tracking de canales
        if event_type == "StasisStart":
            channel_id = event["channel"]["id"]
            self.active_channels[channel_id] = event["channel"]
            logger.info(f"Channel {channel_id} entered Stasis")

        elif event_type == "StasisEnd":
            channel_id = event["channel"]["id"]
            if channel_id in self.active_channels:
                del self.active_channels[channel_id]
            logger.info(f"Channel {channel_id} left Stasis")

        elif event_type == "ChannelDestroyed":
            channel_id = event["channel"]["id"]
            if channel_id in self.active_channels:
                del self.active_channels[channel_id]
            logger.info(f"Channel {channel_id} destroyed")

        # Ejecutar handlers registrados
        if event_type in self.event_handlers:
            channel = event.get("channel")
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event, channel)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")

    async def listen_events(self):
        """Escucha eventos WebSocket de ARI"""
        params = {
            "app": self.app_name,
            "subscribeAll": "true"
        }

        while True:
            try:
                logger.info(f"Connecting to ARI WebSocket: {self.ws_url}")

                async with self.session.ws_connect(
                    self.ws_url,
                    params=params,
                    heartbeat=30
                ) as ws:
                    self.ws = ws
                    logger.info("ARI WebSocket connected")

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                event = json.loads(msg.data)
                                await self._handle_event(event)
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON: {msg.data}")

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break

                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("WebSocket closed")
                            break

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")

            # Reconectar después de 5 segundos
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

    # ============================================
    # CHANNEL OPERATIONS
    # ============================================

    async def originate_call(
        self,
        endpoint: str,
        extension: str = None,
        context: str = "call-center",
        caller_id: str = None,
        timeout: int = 30,
        variables: dict = None
    ) -> dict:
        """
        Origina una llamada saliente

        Args:
            endpoint: Endpoint a llamar (ej: "PJSIP/5551234@trunk-endpoint")
            extension: Extensión de destino (opcional)
            context: Contexto del dialplan
            caller_id: Caller ID (opcional)
            timeout: Timeout en segundos
            variables: Variables de canal (opcional)

        Returns:
            dict: Información del canal creado

        Example:
            channel = await client.originate_call(
                endpoint="PJSIP/5551234@trunk-endpoint",
                caller_id="Call Center <100>",
                variables={"CUSTOMER_ID": "12345"}
            )
        """
        url = f"{self.base_url}/channels"

        data = {
            "endpoint": endpoint,
            "app": self.app_name,
            "timeout": timeout
        }

        if extension:
            data["extension"] = extension
            data["context"] = context

        if caller_id:
            data["callerId"] = caller_id

        if variables:
            data["variables"] = variables

        async with self.session.post(url, json=data) as resp:
            if resp.status == 200:
                channel = await resp.json()
                logger.info(f"Call originated: {channel['id']}")
                return channel
            else:
                error = await resp.text()
                logger.error(f"Failed to originate call: {error}")
                raise Exception(f"Originate failed: {error}")

    async def answer_channel(self, channel_id: str):
        """Contesta un canal"""
        url = f"{self.base_url}/channels/{channel_id}/answer"
        async with self.session.post(url) as resp:
            if resp.status == 204:
                logger.info(f"Channel {channel_id} answered")
            else:
                logger.error(f"Failed to answer {channel_id}")

    async def hangup_channel(self, channel_id: str, reason: str = "normal"):
        """Cuelga un canal"""
        url = f"{self.base_url}/channels/{channel_id}"
        params = {"reason": reason}
        async with self.session.delete(url, params=params) as resp:
            if resp.status == 204:
                logger.info(f"Channel {channel_id} hung up")
            else:
                logger.error(f"Failed to hangup {channel_id}")

    async def play_media(
        self,
        channel_id: str,
        media: str,
        lang: str = "es"
    ) -> dict:
        """
        Reproduce audio en un canal

        Args:
            channel_id: ID del canal
            media: URI del audio (ej: "sound:welcome" o "recording:my-audio")
            lang: Idioma (default: es)

        Returns:
            dict: Información del playback
        """
        url = f"{self.base_url}/channels/{channel_id}/play"
        data = {
            "media": f"{media}",
            "lang": lang
        }

        async with self.session.post(url, json=data) as resp:
            if resp.status == 201:
                playback = await resp.json()
                logger.info(f"Playing {media} on {channel_id}")
                return playback
            else:
                logger.error(f"Failed to play media on {channel_id}")
                return None

    # ============================================
    # RECORDING
    # ============================================

    async def start_recording(
        self,
        channel_id: str,
        name: str = None,
        format: str = "wav",
        max_duration: int = 3600,
        beep: bool = False
    ) -> dict:
        """
        Inicia grabación de un canal

        Args:
            channel_id: ID del canal
            name: Nombre del archivo (auto-generado si None)
            format: Formato de audio (wav, gsm, etc.)
            max_duration: Duración máxima en segundos
            beep: Reproducir beep antes de grabar

        Returns:
            dict: Información de la grabación
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"recording_{channel_id}_{timestamp}"

        url = f"{self.base_url}/channels/{channel_id}/record"
        data = {
            "name": name,
            "format": format,
            "maxDurationSeconds": max_duration,
            "beep": beep,
            "terminateOn": "none"
        }

        async with self.session.post(url, json=data) as resp:
            if resp.status == 201:
                recording = await resp.json()
                logger.info(f"Recording started: {name}")
                return recording
            else:
                logger.error(f"Failed to start recording on {channel_id}")
                return None

    async def stop_recording(self, recording_name: str):
        """Detiene una grabación"""
        url = f"{self.base_url}/recordings/live/{recording_name}/stop"
        async with self.session.post(url) as resp:
            if resp.status == 204:
                logger.info(f"Recording stopped: {recording_name}")
            else:
                logger.error(f"Failed to stop recording {recording_name}")

    # ============================================
    # BRIDGES
    # ============================================

    async def create_bridge(self, bridge_type: str = "mixing") -> dict:
        """
        Crea un bridge para conectar canales

        Args:
            bridge_type: Tipo de bridge (mixing, holding, etc.)

        Returns:
            dict: Información del bridge
        """
        url = f"{self.base_url}/bridges"
        data = {"type": bridge_type}

        async with self.session.post(url, json=data) as resp:
            if resp.status == 200:
                bridge = await resp.json()
                logger.info(f"Bridge created: {bridge['id']}")
                return bridge
            else:
                logger.error("Failed to create bridge")
                return None

    async def add_channel_to_bridge(self, bridge_id: str, channel_id: str):
        """Añade un canal a un bridge"""
        url = f"{self.base_url}/bridges/{bridge_id}/addChannel"
        data = {"channel": channel_id}

        async with self.session.post(url, json=data) as resp:
            if resp.status == 204:
                logger.info(f"Channel {channel_id} added to bridge {bridge_id}")
            else:
                logger.error(f"Failed to add channel to bridge")

    async def remove_channel_from_bridge(self, bridge_id: str, channel_id: str):
        """Remueve un canal de un bridge"""
        url = f"{self.base_url}/bridges/{bridge_id}/removeChannel"
        data = {"channel": channel_id}

        async with self.session.post(url, json=data) as resp:
            if resp.status == 204:
                logger.info(f"Channel {channel_id} removed from bridge {bridge_id}")
            else:
                logger.error(f"Failed to remove channel from bridge")

    async def destroy_bridge(self, bridge_id: str):
        """Destruye un bridge"""
        url = f"{self.base_url}/bridges/{bridge_id}"
        async with self.session.delete(url) as resp:
            if resp.status == 204:
                logger.info(f"Bridge {bridge_id} destroyed")
            else:
                logger.error(f"Failed to destroy bridge")

    # ============================================
    # TRANSFER
    # ============================================

    async def transfer_to_extension(
        self,
        channel_id: str,
        extension: str,
        context: str = "call-center"
    ):
        """
        Transfiere una llamada a una extensión

        Args:
            channel_id: ID del canal
            extension: Extensión de destino (ej: "200" para agente humano)
            context: Contexto del dialplan
        """
        # Crear bridge
        bridge = await self.create_bridge()
        if not bridge:
            return False

        bridge_id = bridge["id"]

        # Añadir canal actual al bridge
        await self.add_channel_to_bridge(bridge_id, channel_id)

        # Originar llamada a extensión
        try:
            new_channel = await self.originate_call(
                endpoint=f"PJSIP/{extension}",
                context=context
            )

            # Añadir nuevo canal al bridge
            await self.add_channel_to_bridge(bridge_id, new_channel["id"])

            logger.info(f"Transfer completed: {channel_id} -> {extension}")
            return True

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            await self.destroy_bridge(bridge_id)
            return False

    # ============================================
    # STATUS
    # ============================================

    async def get_channels(self) -> list:
        """Obtiene lista de todos los canales activos"""
        url = f"{self.base_url}/channels"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                channels = await resp.json()
                return channels
            return []

    async def get_channel_info(self, channel_id: str) -> dict:
        """Obtiene información de un canal específico"""
        url = f"{self.base_url}/channels/{channel_id}"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

    # ============================================
    # RUN
    # ============================================

    async def run(self):
        """Ejecuta el cliente ARI (blocking)"""
        await self.listen_events()


# ============================================
# EJEMPLO DE USO
# ============================================

async def example_usage():
    """Ejemplo de integración con el call center"""

    client = ARIClient()
    await client.connect()

    # Handler para llamadas entrantes
    @client.on("StasisStart")
    async def on_call_start(event, channel):
        channel_id = channel["id"]
        caller = channel["caller"]["number"]

        logger.info(f"📞 Nueva llamada de {caller}")

        # Contestar
        await client.answer_channel(channel_id)

        # Iniciar grabación si es necesario
        # await client.start_recording(channel_id)

        # Reproducir mensaje de bienvenida
        # await client.play_media(channel_id, "sound:welcome")

        # Aquí se integraría con el AudioSocket existente
        # para el procesamiento de IA (STT -> LLM -> TTS)

    # Handler para cuando cuelgan
    @client.on("ChannelHangupRequest")
    async def on_hangup(event, channel):
        channel_id = channel["id"]
        logger.info(f"📴 Hangup: {channel_id}")

    # Handler para DTMF (teclas presionadas)
    @client.on("ChannelDtmfReceived")
    async def on_dtmf(event, channel):
        digit = event["digit"]
        logger.info(f"🔢 DTMF: {digit}")

        # Ejemplo: Presionar 0 para agente humano
        if digit == "0":
            await client.transfer_to_extension(channel["id"], "200")

    # Ejecutar
    await client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())
