"""
app.py — Flask Backend for NeuralChat AI Assistant
====================================================
Powered by Google Gemini AI — a friendly, general-purpose chatbot.

Endpoints:
  POST /chat          — Send a message, get an AI response
  GET  /api/config    — Check Gemini status
  GET  /api/stats     — Chat statistics for dashboard
  GET  /admin         — Admin dashboard page
  GET  /              — Main chat page

Run:
  python app.py
"""

import os
import uuid
import logging
import threading
import time
import requests
from datetime import datetime, timezone, timedelta

from flask import (
    Flask, request, jsonify, render_template,
    session, send_from_directory
)
from flask_cors import CORS
from sqlalchemy import func

from database import db, Conversation, FAQ, IntentStat, seed_faqs, seed_intent_stats, seed_demo_data
from gemini_engine import get_gemini_response, is_gemini_available, clear_session

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR    = os.path.join(BASE_DIR, 'static')

# ── Flask App Setup ───────────────────────────────────────────────────────────
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'neuralchat-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'chatbot.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

CORS(app)
db.init_app(app)

# ── Gemini Status ─────────────────────────────────────────────────────────────
GEMINI_ENABLED = is_gemini_available()
logger.info(f"Gemini AI: {'ENABLED' if GEMINI_ENABLED else 'DISABLED (set GOOGLE_API_KEY)'}")

# Fallback when Gemini is unavailable
FALLBACK_RESPONSES = [
    "I'm having trouble connecting to my AI brain right now. Please make sure the Gemini API key is configured correctly in the .env file!",
    "Oops! My AI engine isn't responding. Check that GOOGLE_API_KEY is set in the .env file.",
    "I can't generate a smart response right now — my Gemini AI connection seems to be down. Try again in a moment!",
]

import random


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE: POST /chat — Main Chat API
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/chat', methods=['POST'])
def chat():
    """
    Accepts JSON: { "message": "user message", "session_id": "optional" }
    Returns JSON: { "response": "AI reply", "source": "gemini" | "fallback" }
    """
    data = request.get_json(silent=True)
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing "message" field'}), 400

    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Session ID for conversation history
    session_id = data.get('session_id') or session.get('session_id') or str(uuid.uuid4())
    session['session_id'] = session_id

    # ── Get response from Gemini AI ───────────────────────────────────────────
    if GEMINI_ENABLED:
        result = get_gemini_response(
            user_message=user_message,
            session_id=session_id
        )
        if result['source'] == 'gemini' and result['response']:
            bot_response = result['response']
            response_source = 'gemini'
            logger.info(f"Gemini response for: '{user_message[:50]}...'")
        else:
            bot_response = random.choice(FALLBACK_RESPONSES)
            response_source = 'fallback'
            logger.warning(f"Gemini error: {result.get('error', 'unknown')}")
    else:
        bot_response = random.choice(FALLBACK_RESPONSES)
        response_source = 'fallback'

    # ── Save to Database ───────────────────────────────────────────────────────
    try:
        convo = Conversation(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response,
            detected_intent='gemini' if response_source == 'gemini' else 'fallback',
            confidence=1.0 if response_source == 'gemini' else 0.0
        )
        db.session.add(convo)

        # Update stats
        stat = IntentStat.query.filter_by(intent='gemini').first()
        if stat:
            stat.count += 1
        else:
            db.session.add(IntentStat(intent='gemini', count=1))

        db.session.commit()
    except Exception as e:
        logger.error(f"DB error: {e}")
        db.session.rollback()

    return jsonify({
        'response': bot_response,
        'source': response_source
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE: GET /api/config — Check AI status
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'gemini_enabled': GEMINI_ENABLED,
        'model_name': 'gemini-2.5-flash' if GEMINI_ENABLED else None
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE: GET /api/stats — Dashboard analytics
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total = Conversation.query.count()

    intent_stats = IntentStat.query.order_by(IntentStat.count.desc()).all()
    intent_data = [s.to_dict() for s in intent_stats]

    recent = (Conversation.query
              .order_by(Conversation.timestamp.desc())
              .limit(20).all())

    daily_volume = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = (Conversation.query
                 .filter(Conversation.timestamp.between(day_start, day_end))
                 .count())
        daily_volume.append({'date': day.strftime('%b %d'), 'count': count})

    return jsonify({
        'total_conversations': total,
        'intent_distribution': intent_data,
        'recent_conversations': [c.to_dict() for c in recent],
        'daily_volume': daily_volume
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE: GET /api/faqs
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    category = request.args.get('category')
    if category:
        faqs = FAQ.query.filter_by(category=category).all()
    else:
        faqs = FAQ.query.all()
    return jsonify([f.to_dict() for f in faqs])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'message': 'NeuralChat server is alive'}), 200


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


# ── App Initialisation & Heartbeat ───────────────────────────────────────────
def keep_alive():
    """Ping /ping every 14 min to prevent Render free-tier from sleeping."""
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://ai-chatbot-06fq.onrender.com')
    logger.info(f"Heartbeat starting — will ping {RENDER_URL}/ping every 14 min")
    time.sleep(60)  # Wait for server to fully boot
    while True:
        try:
            r = requests.get(f"{RENDER_URL}/ping", timeout=10)
            logger.info(f"[Heartbeat] ping → {r.status_code}")
        except Exception as e:
            logger.error(f"[Heartbeat] ping failed: {e}")
        time.sleep(14 * 60)  # 14 minutes


def init_app():
    with app.app_context():
        db.create_all()
        seed_faqs()
        seed_intent_stats(['gemini', 'fallback'])
        from database import seed_demo_data
        seed_demo_data()
        logger.info("Database initialised.")

    # Start keepalive thread (daemon so it dies with the process)
    threading.Thread(target=keep_alive, daemon=True).start()


# ── Initialise on import (works for both gunicorn and direct run) ─────────────
init_app()


if __name__ == '__main__':
    logger.info("Starting NeuralChat on http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)
