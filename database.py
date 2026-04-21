"""
database.py — SQLite Database Setup with SQLAlchemy
====================================================
Defines ORM models and initialises the SQLite database.

Tables:
  - conversations : stores every chat message (user + bot)
  - faqs          : stores frequently asked question pairs
  - intent_stats  : tracks intent frequency for dashboard

Team Module: Database Engineer
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# ── SQLAlchemy instance (initialised in app.py via db.init_app) ───────────────
db = SQLAlchemy()


# ═══════════════════════════════════════════════════════════════════════════════
# Model 1: Conversation — stores every chat exchange
# ═══════════════════════════════════════════════════════════════════════════════
class Conversation(db.Model):
    """
    Records each message pair (user query + bot response).
    One row = one user message with its corresponding bot reply.
    """
    __tablename__ = 'conversations'

    id            = db.Column(db.Integer, primary_key=True)
    session_id    = db.Column(db.String(64), nullable=False, index=True)   # browser session
    user_message  = db.Column(db.Text, nullable=False)
    bot_response  = db.Column(db.Text, nullable=False)
    detected_intent = db.Column(db.String(50), nullable=True)              # classified intent tag
    confidence    = db.Column(db.Float, nullable=True)                     # model confidence %
    timestamp     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':              self.id,
            'session_id':      self.session_id,
            'user_message':    self.user_message,
            'bot_response':    self.bot_response,
            'detected_intent': self.detected_intent,
            'confidence':      round(self.confidence * 100, 1) if self.confidence else None,
            'timestamp':       self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Model 2: FAQ — stores curated question-answer pairs
# ═══════════════════════════════════════════════════════════════════════════════
class FAQ(db.Model):
    """
    Static knowledge base of Frequently Asked Questions.
    Admin can add/edit FAQs from the dashboard.
    """
    __tablename__ = 'faqs'

    id       = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)    # e.g. 'admissions', 'fees'
    question = db.Column(db.Text, nullable=False)
    answer   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':       self.id,
            'category': self.category,
            'question': self.question,
            'answer':   self.answer
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Model 3: IntentStat — tracks how often each intent is triggered
# ═══════════════════════════════════════════════════════════════════════════════
class IntentStat(db.Model):
    """
    Aggregated intent usage counter.
    One row per intent tag — incremented on every classification.
    Used by the admin dashboard Chart.js charts.
    """
    __tablename__ = 'intent_stats'

    id     = db.Column(db.Integer, primary_key=True)
    intent = db.Column(db.String(50), unique=True, nullable=False)
    count  = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'intent': self.intent,
            'count':  self.count
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: Seed FAQ data
# ═══════════════════════════════════════════════════════════════════════════════
SEED_FAQS = [
    ("admissions", "What is the last date to apply?",   "The admission deadline is July 31st for all undergraduate programs."),
    ("admissions", "What documents are needed?",         "Marksheets (10th & 12th), Transfer Certificate, Migration Certificate, ID Proof, and 4 passport photos."),
    ("fees",       "Can I pay fees in installments?",   "Yes, B.Tech fees can be paid in 2 installments — 60% at the start, 40% by November 30th."),
    ("fees",       "Is there a late fee penalty?",       "Yes, a penalty of ₹50 per day is charged after the due date."),
    ("courses",    "What is the duration of B.Tech?",   "The B.Tech program is 4 years (8 semesters)."),
    ("courses",    "Is lateral entry available?",        "Yes, diploma holders can take lateral entry into the 2nd year of B.Tech."),
    ("library",    "What is the library fine amount?",   "The fine is ₹2 per day per book for overdue returns."),
    ("hostel",     "Is Wi-Fi available in the hostel?",  "Yes, high-speed Wi-Fi (100 Mbps) is available in all hostel rooms."),
    ("exams",      "What are passing marks?",            "You need at least 40% in each subject (14/35 in internal, 26/65 in end-term) to pass."),
    ("contact",    "What is the college email?",         "info@neuralcollege.edu.in — for general enquiries. Admissions: admissions@neuralcollege.edu.in"),
]


def seed_faqs():
    """Insert default FAQs if table is empty."""
    if FAQ.query.count() == 0:
        for category, question, answer in SEED_FAQS:
            db.session.add(FAQ(category=category, question=question, answer=answer))
        db.session.commit()
        print("[DB] Seeded FAQ table with default data.")


def seed_intent_stats(intents: list):
    """Ensure every intent has a row in intent_stats (count starts at 0)."""
    for tag in intents:
        existing = IntentStat.query.filter_by(intent=tag).first()
        if not existing:
            db.session.add(IntentStat(intent=tag, count=0))
    db.session.commit()


def seed_demo_data():
    """Seed realistic demo conversations and intent stats for the dashboard."""
    if Conversation.query.count() > 0:
        return  # Already has data

    import random
    from datetime import timedelta

    demo_chats = [
        ("Tell me a joke!", "Why don't scientists trust atoms? Because they make up everything! 😄", "gemini"),
        ("What's the meaning of life?", "That's one of humanity's biggest questions! Many philosophers suggest it's about finding purpose, connection, and happiness.", "gemini"),
        ("Help me study for my math exam", "Here are some tips: 1) Practice problems daily, 2) Understand concepts, don't memorize, 3) Use spaced repetition, 4) Teach someone else!", "gemini"),
        ("Recommend a movie", "I'd recommend 'Interstellar' — it's a stunning sci-fi masterpiece about space, time, and love. Perfect for a movie night! 🎬", "gemini"),
        ("How do I learn Python?", "Start with the basics: variables, loops, functions. Use resources like Python.org tutorials, freeCodeCamp, or Codecademy.", "gemini"),
        ("Give me motivation", "Every expert was once a beginner. Keep showing up, keep trying, and you'll look back amazed at how far you've come! 💪", "gemini"),
        ("What is machine learning?", "Machine learning is a branch of AI where computers learn patterns from data without being explicitly programmed.", "gemini"),
        ("Tell me a fun fact", "Honey never spoils! Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible. 🍯", "gemini"),
        ("How to be more productive?", "Try the Pomodoro technique: work 25 minutes, break 5 minutes. Also, prioritize your top 3 tasks each morning!", "gemini"),
        ("Write a short poem", "Beneath the stars so bright,\nDreams take their gentle flight,\nThrough shadows soft and deep,\nThe world begins to sleep. ✨", "gemini"),
        ("What's the weather like?", "I can't check real-time weather, but you can ask Google or check weather.com for your area!", "gemini"),
        ("Help me with my resume", "Key tips: 1) Use action verbs, 2) Quantify achievements, 3) Tailor it to each job, 4) Keep it to 1-2 pages.", "gemini"),
        ("Hi there!", "Hey! Great to see you! 👋 How can I help you today? I'm ready for anything — jokes, advice, study help, you name it!", "gemini"),
        ("What's 2+2?", "4! Though if we're talking about higher mathematics, there are some interesting abstract algebra systems where that's not always the case 😄", "gemini"),
        ("Best programming language", "It depends on your goal! Python for AI/data, JavaScript for web, Swift for iOS, Rust for systems. Python is the most beginner-friendly.", "gemini"),
    ]

    now = datetime.utcnow()
    for i, (user_msg, bot_msg, intent) in enumerate(demo_chats):
        # Spread conversations over the past 7 days
        days_ago = random.randint(0, 6)
        hours_ago = random.randint(0, 23)
        ts = now - timedelta(days=days_ago, hours=hours_ago)

        convo = Conversation(
            session_id=f"demo-session-{random.randint(1, 5)}",
            user_message=user_msg,
            bot_response=bot_msg,
            detected_intent=intent,
            confidence=random.uniform(0.85, 0.99),
            timestamp=ts
        )
        db.session.add(convo)

    # Seed realistic intent stats
    intent_categories = {
        'gemini': random.randint(45, 120),
        'general_knowledge': random.randint(20, 50),
        'jokes_fun': random.randint(15, 40),
        'study_help': random.randint(18, 45),
        'advice': random.randint(12, 35),
        'recommendations': random.randint(10, 30),
        'creative_writing': random.randint(8, 25),
        'coding_help': random.randint(10, 30),
    }

    for intent, count in intent_categories.items():
        existing = IntentStat.query.filter_by(intent=intent).first()
        if existing:
            existing.count = count
        else:
            db.session.add(IntentStat(intent=intent, count=count))

    db.session.commit()
    print("[DB] Seeded demo conversations and intent stats.")
