from __future__ import annotations

import asyncio
import base64
import binascii
import json
from io import BytesIO
import wave
import uuid
from typing import Any, Awaitable, Callable, Optional

import websockets
from openai import OpenAI

from .config import AppConfig
from .realtime_handlers import fanout_event_handler
from .realtime_pipeline import RealtimeScenarioPipeline
from .realtime_session import RealtimeConfig, RealtimeSessionManager, RealtimeWebSocketClient
from .audio_relay import RealtimeAudioRelay
from .fallbacks import build_realtime_error_handler
from .factory import build_scenario_builder
from .logging_utils import get_logger
from .scenario_builder import ScenarioBuilder

ClientSender = Callable[[dict[str, Any]], Awaitable[None]]


async def relay_server(host: str, port: int, stop_event: Optional[asyncio.Event] = None) -> None:
    async def handler(client_ws):
        await handle_client(client_ws)

    async with websockets.serve(handler, host, port):
        logger = get_logger("realtime_bridge")
        logger.info("Realtime relay listening on ws://%s:%s", host, port)
        if stop_event is None:
            await asyncio.Future()
        else:
            await stop_event.wait()


async def handle_client(client_ws) -> None:
    logger = get_logger("realtime_bridge")
    client_peer = getattr(client_ws, "remote_address", None)
    client_id = _new_client_id()
    logger.info("Client connected [%s]: %s", client_id, client_peer)

    config = AppConfig.from_env()
    session_info = RealtimeSessionManager(
        RealtimeConfig(api_key=config.api_key, model=config.realtime_model, max_retries=config.max_retries)
    ).create_session()

    use_server_vad = True
    session_config = {
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "turn_detection": {"type": "server_vad", "create_response": False},
        "input_audio_transcription": {"model": "whisper-1"},
    }

    openai_client = RealtimeWebSocketClient(
        session=session_info,
        api_key=config.api_key,
        event_handler=lambda _: None,
        session_config=session_config,
        max_retries=config.max_retries,
    )

    async def send_to_client(payload: dict[str, Any]) -> None:
        await client_ws.send(json.dumps(payload))

    state = {
        "has_audio": False,
        "total_bytes": 0,
        "sample_rate": 24000,
        "speaking": False,
        "completed_sent": False,
    }

    async def on_transcript(text: str, is_final: bool) -> None:
        payload = {
            "type": "response.audio_transcript.done" if is_final else "response.audio_transcript.delta",
            "transcript": text if is_final else None,
            "transcript_delta": text if not is_final else None,
        }
        await send_to_client(payload)

    audio_relay = RealtimeAudioRelay(
        on_audio_chunk_base64=lambda chunk: send_to_client({"type": "response.audio.delta", "delta": chunk}),
        on_transcript=on_transcript,
    )

    builder = build_scenario_builder(
        api_key=config.api_key,
        model=config.llm_model,
        max_attempts=config.max_attempts,
        logger=logger,
    )

    tts_client = OpenAI(api_key=config.api_key)

    async def send_response(text: str) -> None:
        audio_bytes, sample_rate = await asyncio.to_thread(_tts_pcm16_from_text, tts_client, text)
        await _send_pcm16_audio(send_to_client, audio_bytes, sample_rate=sample_rate)
        if not state.get("completed_sent"):
            await send_to_client(
                {
                    "type": "response.audio_transcript.done",
                    "transcript": text,
                }
            )

    async def on_complete(scenario_builder: ScenarioBuilder) -> None:
        scenario_builder.ensure_defaults()
        state_snapshot = scenario_builder.state
        logger.info("Scenario completed [%s]", client_id)
        await send_to_client(
            {
                "type": "scenario.completed",
                "json": {
                    "place": state_snapshot.place,
                    "conversation_partner": state_snapshot.partner,
                    "conversation_goal": state_snapshot.goal,
                },
                "completed": True,
            }
        )
        state["completed_sent"] = True
        await openai_client.close()

    pipeline = RealtimeScenarioPipeline(builder, send_response, on_complete=on_complete)
    async def forward_user_transcript(event: dict[str, Any]) -> None:
        event_type = event.get("type", "")
        if event_type in (
            "input_audio_buffer.transcription.completed",
            "conversation.item.input_audio_transcription.completed",
        ):
            transcript = event.get("transcript")
            if isinstance(transcript, str) and transcript.strip():
                if builder.state.completed:
                    return
                await send_to_client({"type": "input_audio.transcript", "transcript": transcript})

    ready_event = asyncio.Event()
    session_ready = {"updated": False, "cleared": False}

    async def log_event_type(event: dict[str, Any]) -> None:
        event_type = event.get("type", "unknown")
        if event_type == "session.updated":
            session_ready["updated"] = True
            await openai_client.send_event({"type": "input_audio_buffer.clear"})
        if event_type == "input_audio_buffer.cleared":
            session_ready["cleared"] = True
        if session_ready["updated"] and session_ready["cleared"]:
            ready_event.set()
        if event_type == "error":
            logger.error("OpenAI error [%s]: %s", client_id, event)
        if event_type == "response.audio.delta":
            state["speaking"] = True
        if event_type == "response.audio.done":
            state["speaking"] = False

    openai_client.set_event_handler(
        fanout_event_handler(
            [log_event_type, audio_relay.handle_event, forward_user_transcript, pipeline.handle_event]
        )
    )
    openai_client.set_error_handler(build_realtime_error_handler(send_to_client))

    openai_task = asyncio.create_task(openai_client.connect_and_run())
    connected = await openai_client.wait_until_connected(timeout=10.0)
    if not connected:
        await client_ws.send(json.dumps({"type": "error", "message": "Realtime connection timeout"}))
        await openai_client.close()
        openai_task.cancel()
        return
    ready = await _wait_ready(ready_event, timeout=10.0)
    if not ready:
        await client_ws.send(json.dumps({"type": "error", "message": "Realtime session not ready"}))
        await openai_client.close()
        openai_task.cancel()
        return
    await client_ws.send(json.dumps({"type": "ready"}))
    try:
        async for message in client_ws:
            # logger.info("Client event: %s", _safe_event_type(message))
            await handle_client_message(message, openai_client, state, use_server_vad)
    finally:
        await openai_client.close()
        openai_task.cancel()


async def handle_client_message(
    message: str,
    openai_client: RealtimeWebSocketClient,
    state: dict[str, bool],
    use_server_vad: bool,
) -> None:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return

    msg_type = payload.get("type")
    if msg_type == "input_audio_chunk":
        if state.get("speaking"):
            return
        audio = payload.get("audio")
        sample_rate = payload.get("sample_rate")
        if isinstance(sample_rate, int) and sample_rate > 0:
            state["sample_rate"] = sample_rate
        if isinstance(audio, str) and audio:
            try:
                audio_bytes = base64.b64decode(audio)
            except (ValueError, binascii.Error):
                return
            if not audio_bytes:
                return
            await openai_client.send_event({"type": "input_audio_buffer.append", "audio": audio})
            state["has_audio"] = True
            state["total_bytes"] += len(audio_bytes)
        return
    if msg_type == "input_audio_commit":
        if state.get("speaking"):
            return
        if use_server_vad:
            return
        if state.get("has_audio"):
            sample_rate = state.get("sample_rate", 24000)
            min_bytes = int(sample_rate * 0.1 * 2)
            if state.get("total_bytes", 0) >= min_bytes:
                await openai_client.send_event({"type": "input_audio_buffer.commit"})
            state["has_audio"] = False
            state["total_bytes"] = 0
        return
    if msg_type == "input_audio_clear":
        if not state.get("has_audio") and state.get("total_bytes", 0) == 0:
            await openai_client.send_event({"type": "input_audio_buffer.clear"})
        else:
            return
    if msg_type == "text":
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            await openai_client.send_event(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "text", "text": text.strip()}],
                    },
                }
            )
        return


def _tts_pcm16_from_text(client: OpenAI, text: str) -> tuple[bytes, int]:
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        response_format="wav",
    )
    wav_bytes = response.read()
    if not wav_bytes:
        return b"", 24000
    with wave.open(BytesIO(wav_bytes), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            return b"", wav.getframerate()
        return wav.readframes(wav.getnframes()), wav.getframerate()


async def _send_pcm16_audio(send_to_client, audio_bytes: bytes, sample_rate: int) -> None:
    if not audio_bytes:
        return
    chunk_ms = 100
    chunk_size = int(sample_rate * (chunk_ms / 1000.0) * 2)
    for offset in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[offset : offset + chunk_size]
        payload = {
            "type": "response.audio.delta",
            "delta": base64.b64encode(chunk).decode("ascii"),
            "sample_rate": sample_rate,
        }
        await send_to_client(payload)
        await asyncio.sleep(chunk_ms / 1000.0)
    await send_to_client({"type": "response.audio.done"})




async def _wait_ready(event: asyncio.Event, timeout: float) -> bool:
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False


def _new_client_id() -> str:
    return uuid.uuid4().hex[:8]
