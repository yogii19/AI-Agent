from flask import Flask, render_template, request, redirect, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
import openai
import os
import PyPDF2

app = Flask(__name__)
app.secret_key = "secret123"

# 🔑 OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🔐 Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Demo users (you can store in DB later)
users = {"admin": {"password": "123"}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 🍃 MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["darshanam_ai"]
collection = db["chats"]

# 🔐 Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect("/")
    return render_template("login.html")
    

# 🚪 Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# 📄 Upload PDF
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["pdf"]

    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    session["pdf_text"] = text
    return redirect("/")

# 💬 Main chat
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        user_input = request.form["message"]

        pdf_context = session.get("pdf_text", "")

        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Darshanam.ai, a smart AI assistant. Use PDF content if relevant."},
                {"role": "user", "content": pdf_context + "\\nUser: " + user_input}
            ]
        )

        response = completion.choices[0].message["content"]

        # Save in DB
        collection.insert_one({
            "user": current_user.id,
            "message": user_input,
            "response": response
        })

    # Load chats
    chats = list(collection.find({"user": current_user.id}))

    return render_template("index.html", chats=chats)

# 🔄 Reset chat
@app.route("/reset")
@login_required
def reset():
    collection.delete_many({"user": current_user.id})
    session.pop("pdf_text", None)
    return redirect("/")

# ▶️ Run app
if __name__ == "__main__":
    app.run()
