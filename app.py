from flask import Flask, render_template, request, session, redirect, jsonify
from flask_mail import Mail, Message
import sqlite3, random, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace_with_a_random_secret")

# -------- Mail configuration (CHANGE THESE) ----------
# Use your Gmail and App Password here (see instructions below)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ailanavyasri06@gmail.com'          # <--- change
app.config['MAIL_PASSWORD'] = 'auwn gfjn chic izxz'        # <--- change (Gmail App Password)
mail = Mail(app)
# -----------------------------------------------------

# --------- Database initialization ----------
DB_PATH = "notes.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    date TEXT,
    encrypted_note TEXT
)
""")
conn.commit()
# --------------------------------------------

@app.route("/")
def index():
    # login page
    return render_template("login.html")


@app.route("/send_otp", methods=["POST"])
def send_otp():
    email = request.form.get("email", "").strip()
    if not email:
        return "Email required", 400

    # generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['email'] = email

    # send OTP email
    try:
        msg = Message("Your Notepad OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your login OTP for Encrypted Notepad is: {otp}\n\nIf you didn't request this, ignore."
        mail.send(msg)
    except Exception as e:
        # helpful error message for debugging
        return f"Failed to send email: {e}", 500

    return render_template("otp.html", email=email)


@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    user_otp = request.form.get("otp", "").strip()
    stored = session.get("otp")
    if stored and user_otp == stored:
        session['logged_in'] = True
        # Keep email in session
        return redirect("/notes")
    return "Wrong OTP. Go back and try again.", 401


@app.route("/notes")
def notes_page():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("notes.html", email=session.get("email"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- Notes API ----------

@app.route("/save_note", methods=["POST"])
def save_note():
    if not session.get("logged_in"):
        return "Not logged in", 401

    email = session.get("email")
    encrypted = request.form.get("encrypted_note", "")
    note_date = request.form.get("date", "")
    if not note_date:
        return "Date missing", 400

    # validate date format roughly (YYYY-MM-DD)
    try:
        datetime.strptime(note_date, "%Y-%m-%d")
    except Exception:
        return "Invalid date format. Use YYYY-MM-DD", 400

    cur.execute("INSERT INTO notes (email, date, encrypted_note) VALUES (?, ?, ?)",
                (email, note_date, encrypted))
    conn.commit()
    return "ok", 200


@app.route("/get_notes")
def get_all_notes():
    if not session.get("logged_in"):
        return jsonify({"notes": []})
    email = session.get("email")
    cur.execute("SELECT encrypted_note, date FROM notes WHERE email=? ORDER BY date DESC", (email,))
    rows = cur.fetchall()
    return jsonify({"notes": [{"date": r[1], "enc": r[0]} for r in rows]})


@app.route("/get_notes_by_date")
def get_notes_by_date():
    if not session.get("logged_in"):
        return jsonify({"notes": []})
    email = session.get("email")
    date = request.args.get("date", "")
    cur.execute("SELECT encrypted_note FROM notes WHERE email=? AND date=? ORDER BY id DESC", (email, date))
    rows = cur.fetchall()
    return jsonify({"notes": [r[0] for r in rows]})

# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
