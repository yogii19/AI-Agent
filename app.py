from flask import Flask, render_template, request, redirect, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ OpenAI setup (IMPORTANT)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔐 Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# 👤 Demo user
users = {"admin": {"password": "123"}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 🔐 Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# 🚪 Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# 💬 AI Chat
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if "chats" not in session:
        session["chats"] = []

    if request.method == "POST":
        user_input = request.form.get("message")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Darshanam.ai, a helpful AI assistant."},
                    *[
                        {"role": "user", "content": c["user"]} if i % 2 == 0 
                        else {"role": "assistant", "content": c["bot"]}
                        for i, c in enumerate(session["chats"])
                    ],
                    {"role": "user", "content": user_input}
                ]
            )

            reply = response.choices[0].message.content

        except Exception as e:
            print("AI ERROR:", e)
            reply = "Error connecting to AI. Check API key."

        session["chats"].append({
            "user": user_input,
            "bot": reply
        })
        session.modified = True

    return render_template("index.html", chats=session["chats"])

# 🔄 Reset chat
@app.route("/reset")
@login_required
def reset():
    session.pop("chats", None)
    return redirect("/")

# ▶️ Run
if __name__ == "__main__":
    app.run(debug=True)
