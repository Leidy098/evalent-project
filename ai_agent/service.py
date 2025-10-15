import json
from typing import Dict, Any

import google.generativeai as genai
from django.conf import settings


# =========================
# CONFIGURACIÓN DEL CLIENTE
# =========================
# Usamos AI Studio (google-generativeai). NO mezclar con Vertex ni gRPC.
# Requiere: pip install -U google-generativeai
genai.configure(api_key=settings.GEMINI_API_KEY)

# Modelos válidos en AI Studio sin prefijo "models/":
# - "gemini-1.5-pro"   (razonamiento más potente)
# - "gemini-1.5-flash" (más veloz y barato)
MODEL_ID = "models/gemini-2.5-flash"


# =========================
# PROMPT Y PARSEO DE RESPUESTA
# =========================
SYSTEM_INSTRUCTIONS = """
Eres un entrevistador profesional. Debes responder SIEMPRE en JSON estricto con esta forma:

{
  "question": "<siguiente pregunta breve y clara>",
  "feedback": "<consejo concreto y accionable sobre la respuesta del candidato>",
  "scores": {
    "claridad": <0-100>,
    "confianza": <0-100>,
    "contenido": <0-100>,
    "creatividad": <0-100>,
    "lenguaje": <0-100>
  }
}

Reglas:
- Devuelve SOLO el JSON. Nada de texto adicional.
- No uses saltos de línea innecesarios fuera del JSON.
- Llena todos los campos y mantén los puntajes como enteros de 0 a 100.
""".strip()


def _fallback_payload() -> Dict[str, Any]:
    """Respuesta de respaldo si el modelo no devuelve JSON válido."""
    return {
        "question": "¿Podrías ampliar tu respuesta con un ejemplo concreto?",
        "feedback": "Organiza tus ideas en 2-3 puntos y justifica con un caso práctico.",
        "scores": {
            "claridad": 50,
            "confianza": 50,
            "contenido": 50,
            "creatividad": 50,
            "lenguaje": 50,
        },
    }


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Intenta extraer JSON del texto devuelto por el modelo."""
    if not text:
        return _fallback_payload()

    text = text.strip()

    # Caso ideal: todo el texto es JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Caso alterno: el modelo devolvió algo con JSON embebido -> heurística simple
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return _fallback_payload()

    return _fallback_payload()


# =========================
# FUNCIÓN PÚBLICA
# =========================
def generate_ai_response(interview, user_message: str) -> Dict[str, Any]:
    """
    Genera la siguiente pregunta, feedback y puntuaciones a partir de la interacción del usuario.
    Devuelve SIEMPRE un dict con las claves: question, feedback, scores.
    """
    # Construimos un prompt compacto: instrucciones + contexto + mensaje del usuario.
    # Con AI Studio, no uses 'models/...', solo el ID simple (p.ej. "gemini-1.5-pro").
    model = genai.GenerativeModel(
        MODEL_ID,
        system_instruction=SYSTEM_INSTRUCTIONS,
    )

    # Puedes ajustar los parámetros si lo deseas (temperatura, top_p, etc.)
    # Aquí usamos el call simple; si quieres más control, usa generate_content({'contents': ...}, generation_config=...)
    try:
        response = model.generate_content(
            [
                # Mensaje del usuario (tu app puede incluir más contexto de 'interview' si hace falta)
                {"role": "user", "parts": [f"Mensaje del candidato: {user_message}"]},
            ]
        )
    except Exception as e:
        # Si hay cualquier error de red/credenciales/etc., devolvemos fallback
        return _fallback_payload()

    # Extraer el texto
    text = ""
    try:
        # Formato usual del SDK
        text = getattr(response, "text", "") or ""
        if not text and getattr(response, "candidates", None):
            # Respaldo por si cambia el formato
            cand = response.candidates[0]
            if cand and getattr(cand, "content", None) and cand.content.parts:
                part = cand.content.parts[0]
                text = getattr(part, "text", "") or ""
    except Exception:
        pass

    # Parseo robusto del JSON
    data = _safe_parse_json(text)

    # Normalización mínima de claves por si el modelo cambió nombres
    data.setdefault("question", _fallback_payload()["question"])
    data.setdefault("feedback", _fallback_payload()["feedback"])
    data.setdefault("scores", _fallback_payload()["scores"])

    # Asegurar que scores tenga todas las subclaves
    for k in ["claridad", "confianza", "contenido", "creatividad", "lenguaje"]:
        data["scores"].setdefault(k, 50)

    return data
