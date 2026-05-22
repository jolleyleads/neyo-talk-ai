from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "neyo-talk-demo-secret")

db_url = os.getenv("DATABASE_URL", "sqlite:///neyo_talk.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_text = db.Column(db.Text)
    bot_text = db.Column(db.Text)
    mode = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedFact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fact = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def call_openai(messages, temperature=0.7):
    if not OPENAI_API_KEY:
        last = messages[-1]["content"]
        return (
            "Neyo Talk is running in demo mode because OPENAI_API_KEY is not set. "
            "I can still store memory, generate structured drafts, and show the interface. "
            f"You said: {last}"
        )

    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature
        }
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45)
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Neyo Talk had an AI connection issue: {str(e)}"

def recent_memory(limit=8):
    rows = Memory.query.order_by(Memory.created_at.desc()).limit(limit).all()
    rows = list(reversed(rows))
    text = ""
    for r in rows:
        text += f"User: {r.user_text}\nNeyo Talk: {r.bot_text}\n"
    return text

def saved_facts(limit=20):
    facts = SavedFact.query.order_by(SavedFact.created_at.desc()).limit(limit).all()
    return "\n".join([f"- {x.fact}" for x in facts])

@app.before_request
def setup():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_text = data.get("message", "")
    mode = data.get("mode", "normal")

    system = """
You are Neyo Talk, a smart AI + synthetic-intelligence-style assistant.
You are helpful, practical, strategic, emotionally intelligent, and clear.
You can help with business automation, coding, websites, scripts, sales, music, research-style thinking, and planning.
Do not claim to have real consciousness. Treat SI as a product/brand concept for synthetic intelligence workflows.
"""

    if mode == "deep":
        system += "\nUse deeper reasoning. Give a structured, step-by-step answer with tradeoffs and the best next action."
    elif mode == "website":
        system += "\nThe user wants website creation. Return clean HTML/CSS/JS or a clear website plan."
    elif mode == "image":
        system += "\nThe user wants an image prompt. Return a vivid image-generation prompt."
    elif mode == "memory":
        system += "\nThe user wants you to remember something. Extract the durable fact and confirm it."

    memory_context = recent_memory()
    facts_context = saved_facts()

    messages = [
        {"role": "system", "content": system},
        {"role": "system", "content": f"Saved facts:\n{facts_context}\n\nRecent conversation:\n{memory_context}"},
        {"role": "user", "content": user_text}
    ]

    answer = call_openai(messages, temperature=0.65)

    if mode == "memory" or user_text.lower().startswith("remember "):
        fact = user_text.replace("remember", "", 1).strip()
        if fact:
            db.session.add(SavedFact(fact=fact))
            db.session.commit()
            answer = f"Saved to Neyo Talk memory: {fact}"

    db.session.add(Memory(user_text=user_text, bot_text=answer, mode=mode))
    db.session.commit()

    return jsonify({"reply": answer, "mode": mode})

@app.route("/api/memories")
def memories():
    facts = SavedFact.query.order_by(SavedFact.created_at.desc()).all()
    chats = Memory.query.order_by(Memory.created_at.desc()).limit(50).all()
    return jsonify({
        "saved_facts": [{"id": f.id, "fact": f.fact, "created_at": f.created_at.isoformat()} for f in facts],
        "recent_chats": [{"user": c.user_text, "bot": c.bot_text, "mode": c.mode, "created_at": c.created_at.isoformat()} for c in chats]
    })

@app.route("/api/clear-memory", methods=["POST"])
def clear_memory():
    Memory.query.delete()
    SavedFact.query.delete()
    db.session.commit()
    return jsonify({"status": "memory_cleared"})

@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "app": "Neyo Talk",
        "features": [
            "chat",
            "voice input",
            "speech output",
            "deep think mode",
            "image prompt mode",
            "website builder mode",
            "SQLite memory",
            "OpenAI optional integration",
            "Render-ready deployment"
        ],
        "openai_configured": bool(OPENAI_API_KEY)
    })

if __name__ == "__main__":
    app.run(debug=True)
