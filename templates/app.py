"""
TEXT TO POT - Flask backend
Endpoints:
 - POST /api/suggest  (body: {"ingredients": "chicken, tomatoes"})
 - GET  /api/recipes
"""

import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import mysql.connector
import requests
from flask_cors import CORS
from datetime import datetime

load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Config from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "texttopot"),
    "auth_plugin": "mysql_native_password"
}

def get_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def log_request(endpoint, payload):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO request_logs (endpoint, payload) VALUES (%s, %s)",
                    (endpoint, json.dumps(payload)))
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, title, ingredients, instructions, source, created_at FROM recipes ORDER BY created_at DESC LIMIT 100;")
        rows = cur.fetchall()
        return jsonify({"ok": True, "recipes": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.route("/api/suggest", methods=["POST"])
def suggest_recipes():
    """
    Accepts JSON: {"ingredients": "chicken, tomatoes"}
    Calls OpenAI text API (legacy-style prompt) and stores up to 3 recipe records.
    """
    data = request.get_json(force=True)
    ingredients = (data.get("ingredients") or "").strip()
    if not ingredients:
        return jsonify({"ok": False, "error": "No ingredients provided."}), 400

    # Basic sanitation / length limit
    if len(ingredients) > 300:
        return jsonify({"ok": False, "error": "Ingredients text too long."}), 400

    prompt = (
        "You're an expert in African home cooking. Given these ingredients: "
        f"{ingredients} "
        "Provide exactly 3 simple, authentic African recipes. "
        "For each recipe return a JSON object with keys: title, ingredients (comma separated list), instructions (concise but complete). "
        "Return a JSON array only, no extra commentary."
    )

    # Call OpenAI (text completion or chat). We'll use completion endpoint (if present).
    # Use a simple request to the OpenAI v1/completions or v1/chat/completions depending on availability.
    try:
        # Prefer chat completion if available — adapt to whichever works for you.
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",  # placeholder; replace with whichever available model
            "messages": [{"role":"user","content": prompt}],
            "temperature": 0.7,
            "max_tokens": 700
        }
        # If your OpenAI endpoint requires a different URL, update accordingly.
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        text = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"ok": False, "error": f"OpenAI request failed: {str(e)}"}), 500

    # Log raw response
    log_request("/api/suggest:openai", {"ingredients": ingredients, "openai_raw": text[:2000]})

    # Robust parse: attempt to parse JSON from model output
    recipes_parsed = []
    try:
        # If model returns a JSON array, parse directly
        # Attempt to find first '[' and last ']' to slice possible JSON.
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            json_text = text[start:end+1]
            candidate = json.loads(json_text)
            if isinstance(candidate, list):
                recipes_parsed = candidate
    except Exception:
        # fallback: try naive split by recipes (best-effort)
        pass

    # Fallback: if parsing failed, try extracting numbered blocks
    if not recipes_parsed:
        # Very naive extraction — split by lines and look for "Title:" style lines
        parts = text.split("\n\n")
        for p in parts:
            lines = [l.strip() for l in p.splitlines() if l.strip()]
            if not lines: continue
            title = lines[0]
            # gather rest
            body = " ".join(lines[1:])
            recipes_parsed.append({"title": title[:200], "ingredients": ingredients, "instructions": body[:2000]})
        # keep at most 3
        recipes_parsed = recipes_parsed[:3]

    # Save to DB
    saved = []
    try:
        conn = get_db()
        cur = conn.cursor()
        for r in recipes_parsed[:3]:
            title = r.get("title") if isinstance(r, dict) else str(r)[:200]
            ingr = r.get("ingredients") if isinstance(r, dict) else ingredients
            instr = r.get("instructions") if isinstance(r, dict) else ""
            cur.execute(
                "INSERT INTO recipes (title, ingredients, instructions, source) VALUES (%s, %s, %s, %s)",
                (title, ingr, instr, "texttopot")
            )
            saved_id = cur.lastrowid
            saved.append({"id": saved_id, "title": title, "ingredients": ingr, "instructions": instr})
        conn.commit()
    except Exception as e:
        return jsonify({"ok": False, "error": f"DB save error: {str(e)}"}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass

    return jsonify({"ok": True, "saved": saved})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
