from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # allow cross-origin if opened as file:// or different port

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT_DIR, "contacts.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


create_table()


# ---------- Static file serving ----------
@app.route("/")
def index():
    return send_from_directory(ROOT_DIR, "frontend.html")


@app.route("/css/<path:filename>")
def css_files(filename: str):
    return send_from_directory(os.path.join(ROOT_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def js_files(filename: str):
    return send_from_directory(os.path.join(ROOT_DIR, "js"), filename)


@app.route("/assets/<path:filename>")
def asset_files(filename: str):
    return send_from_directory(os.path.join(ROOT_DIR, "assets"), filename)


# ---------- API ----------
@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    # Validation
    errors = {}
    if not name:
        errors["name"] = "Name is required"
    if not email or "@" not in email:
        errors["email"] = "Valid email is required"
    if not message or len(message) < 10:
        errors["message"] = "Message must be at least 10 characters"

    if errors:
        return jsonify({"errors": errors}), 400

    # Save to DB
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO contacts (name, email, message, created_at) VALUES (?, ?, ?, ?)",
        (name, email, message, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


@app.route("/messages", methods=["GET"])
def all_messages():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

