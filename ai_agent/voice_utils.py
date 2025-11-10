# ai_agent/voice_utils.py
import base64
import io
from typing import Optional

import google.generativeai as genai
from django.conf import settings


def transcribe_audio(audio_base64: str) -> Optional[str]:
    """
    Transcribe audio usando Gemini.
    
    Args:
        audio_base64: Audio en formato base64
        
    Returns:
        Texto transcrito o None si hay error
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
        
        # Decodificar el audio
        if ',' in audio_base64:
            audio_base64 = audio_base64.split(',')[1]
        
        audio_bytes = base64.b64decode(audio_base64)
        
        # Crear el prompt para transcripción
        prompt = """
        Por favor, transcribe el audio exactamente como se habla.
        Devuelve SOLO el texto transcrito, sin agregar comentarios adicionales.
        """
        
        response = model.generate_content([
            prompt,
            {
                "mime_type": "audio/webm",
                "data": audio_bytes
            }
        ])
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Error en transcripción: {e}")
        return None


def text_to_speech_edge_tts(text: str, language: str = "es") -> Optional[bytes]:
    """
    Convierte texto a voz usando edge-tts (alternativa gratuita).
    
    Args:
        text: Texto a convertir
        language: Código de idioma (es, en)
        
    Returns:
        Audio en bytes o None si hay error
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
        
        # Crear y ejecutar el loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        audio_bytes = loop.run_until_complete(_generate())
        
        return audio_bytes
        
    except Exception as e:
        print(f"Error en edge-tts: {e}")
        return None