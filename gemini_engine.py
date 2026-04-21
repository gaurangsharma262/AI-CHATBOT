"""
gemini_engine.py — Google Gemini AI Integration
=================================================
Powers the chatbot with Google Gemini AI for intelligent,
conversational responses on ANY topic.

Setup:
  1. Get a free API key from https://aistudio.google.com/apikey
  2. Set in .env file:  GOOGLE_API_KEY=your_key_here

Team Module: AI Integration Engineer
"""

import os
import logging

logger = logging.getLogger(__name__)

# ── Try to load API key from .env file ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Initialize Gemini Client ─────────────────────────────────────────────────
_client = None
_MODEL_NAME = "gemini-2.5-flash"


def _get_client():
    """Lazy-initialize the Gemini client."""
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
        logger.warning(
            "GOOGLE_API_KEY not set. Gemini AI disabled. "
            "Get a free key at https://aistudio.google.com/apikey"
        )
        return None

    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        logger.info(f"Gemini client initialized → {_MODEL_NAME}")
        return _client
    except ImportError:
        logger.error("google-genai not installed. Run: pip install google-genai")
        return None
    except Exception as e:
        logger.error(f"Gemini init failed: {e}")
        return None


# ── System Prompt — General-Purpose AI Friend ─────────────────────────────────
SYSTEM_PROMPT = """You are NeuralChat — a friendly, witty, and knowledgeable AI assistant.

Your personality:
- You're like a smart best friend who's always happy to help
- You're warm, conversational, and have a great sense of humor
- You can tell jokes, share fun facts, give life advice, and have deep conversations
- You're enthusiastic and use a casual, friendly tone
- You're honest when you don't know something

You can help with ANYTHING including:
- General knowledge & trivia
- Life advice & motivation
- Jokes, riddles, and fun conversations
- Science, technology, history, geography
- Study tips & academic help
- Coding & programming questions
- Creative writing & brainstorming
- Movie/music/book recommendations
- Health & wellness tips (general, not medical diagnosis)
- Career guidance & interview tips
- Explaining complex topics simply
- Math & problem solving
- Language & grammar help

Guidelines:
- Keep responses concise but helpful (2-4 sentences for simple questions, longer for complex ones)
- Use a friendly, approachable tone — like texting a smart friend
- Feel free to use some emojis occasionally to be expressive 😊
- If asked for jokes, actually tell funny jokes!
- If asked about something harmful or inappropriate, politely decline
- For current events or real-time data, mention that your knowledge has a cutoff
- Format responses in plain text (no markdown)
"""

# ── In-memory conversation history per session ────────────────────────────────
_chat_sessions = {}
MAX_HISTORY_LENGTH = 20


def get_gemini_response(user_message: str, session_id: str = "default") -> dict:
    """
    Get a response from Gemini API.

    Args:
        user_message: The user's raw message
        session_id:   Session ID for conversation continuity

    Returns:
        dict with keys: response (str), source ("gemini" or "error"), model (str)
    """
    client = _get_client()
    if client is None:
        return {
            "response": None,
            "source": "error",
            "model": None,
            "error": "Gemini API not configured"
        }

    try:
        from google.genai import types

        # Build conversation history for context
        if session_id not in _chat_sessions:
            _chat_sessions[session_id] = []

        history = _chat_sessions[session_id]

        # Build the messages list
        contents = []

        # Add conversation history
        for msg in history[-MAX_HISTORY_LENGTH:]:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["text"])]
                )
            )

        # Add current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            )
        )

        # Call Gemini API
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.85,
                max_output_tokens=800,
            )
        )

        bot_reply = response.text.strip() if response.text else None

        if bot_reply:
            # Save to session history
            history.append({"role": "user", "text": user_message})
            history.append({"role": "model", "text": bot_reply})

            # Trim history if too long
            if len(history) > MAX_HISTORY_LENGTH * 2:
                _chat_sessions[session_id] = history[-(MAX_HISTORY_LENGTH * 2):]

            return {
                "response": bot_reply,
                "source": "gemini",
                "model": _MODEL_NAME
            }
        else:
            return {
                "response": None,
                "source": "error",
                "model": _MODEL_NAME,
                "error": "Empty response from Gemini"
            }

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            "response": None,
            "source": "error",
            "model": _MODEL_NAME,
            "error": str(e)
        }


def is_gemini_available() -> bool:
    """Check if Gemini API is configured and ready."""
    return _get_client() is not None


def clear_session(session_id: str):
    """Clear conversation history for a session."""
    _chat_sessions.pop(session_id, None)
