# ai_agent/voice_utils.py
import base64
from typing import Optional
import io

import google.generativeai as genai
from django.conf import settings

from openai import OpenAI  # 👈 nueva librería


# ---------- TRANSCRIPCIÓN (AUDIO -> TEXTO) CON OPENAI (WHISPER / GPT-4O AUDIO) ----------

def transcribe_audio(audio_base64: str) -> Optional[str]:
    """
    Transcribe audio usando la API de OpenAI (Whisper / GPT-4o audio).
    Solo se toca esta parte: el resto de la app sigue igual.
    """
    try:
        if not settings.OPENAI_API_KEY:
            print("❌ No hay OPENAI_API_KEY en settings.")
            return None

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # El audio viene como data URL: "data:audio/webm;base64,AAAA..."
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",")[1]

        audio_bytes = base64.b64decode(audio_base64)

        # Lo envolvemos en un archivo en memoria
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"  # nombre simulado para el archivo

        # Modelo de transcripción:
        # - "gpt-4o-mini-transcribe" (nuevo audio STT)
        # - o "whisper-1" (clásico)
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            # Si quieres forzar español:
            # language="es"
        )

        text = (transcription.text or "").strip()
        print(">> Transcripción OpenAI OK:", text)
        return text or None

    except Exception as e:
        print("❌ Error en transcripción (OpenAI):", e)
        return None


# ---------- TEXTO -> VOZ (SIGUE IGUAL, CON EDGE-TTS) ----------

def text_to_speech_edge_tts(text: str, language: str = "es") -> Optional[bytes]:
    """
    Convierte texto a voz usando edge-tts (alternativa gratuita).
    """
    try:
        import asyncio
        import edge_tts

        async def _generate():
            voice = "es-ES-AlvaroNeural" if language == "es" else "en-US-GuyNeural"
            communicate = edge_tts.Communicate(text, voice)

            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            return audio_data

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_generate())

    except Exception as e:
        print("❌ Error en edge-tts:", e)
        return None
