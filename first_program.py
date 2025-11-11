from flask import Flask, redirect, render_template, request ,session, url_for
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import  LoginManager, UserMixin, logout_user, login_required
from flask_login import login_user
from flask_login import current_user

from flask_migrate import Migrate
from datetime import datetime
from flask_bcrypt import Bcrypt
import os



# -----------------------------
# Flask App Configuration
# -----------------------------
app = Flask(__name__)
app.secret_key = "mysecretkey"  
# Absolute path to make sure database file is valid
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = 'supersecretkey'
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# -----------------------------
# Database Model
# -----------------------------
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Todo {self.id} - {self.title}>"


class User(UserMixin ,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.generate_password_hash(password.encode('utf-8'),bcrypt.gansalt()).decode('utf-8')

    def check_password(self,password):
        return bcrypt.check_password_hash(self.password,password.encode('utf-8'))
    
 


    with app.app_context():
        db.create_all()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
@login_required
def index():
    session["user"] = current_user.name
    todos = Todo.query.all()
    return render_template("index.html", todos=todos, user=current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()  # ✅ Flask-Login ka logout
    session.pop("user", None)
    flash("👋 You have been logged out successfully!", "success")
    return redirect('/login')



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Simple authentication logic (for demonstration purposes)
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            session["user"] = user.name  # user session set karega
            flash("✅ Login successful!", "success")
            return render_template("index.html", user=current_user)
        else:
            flash("❌ Invalid credentials. Please try again.", "danger")
            return redirect("/")
    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")  # ✅ name lena zaroori hai
        email = request.form.get("email")
        password = request.form.get("password")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
# chack existing email 
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("❌ Email already registered. Please use a different email.", "danger")
            return redirect("/register")

        # ✅ ab name include kar ke new user create karo
        new_user = User(name=name, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("✅ Registration successful!", "success")
        return redirect("/login")

    return render_template("register.html")






@app.route("/add", methods=["GET", "POST"])
def add_todo():
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")
        if title and desc:
            todo = Todo(title=title, desc=desc)
            db.session.add(todo)
            db.session.commit()
            flash("✅ Aapka data save ho gaya hai!", "success")
            return redirect("/")
           
    todos = Todo.query.all()
    return render_template("index.html", todos=todos)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_todo(id):
    todo = Todo.query.get_or_404(id)
    if request.method == "POST":
        todo.title = request.form['title']
        todo.desc = request.form['desc']
        db.session.commit()
        flash("✅ Record successfully updated!", "success")
        return redirect('/')
    return render_template("edit.html", todo=todo)


@app.route("/delete/<int:id>")
def delete_todo(id):
    todo = Todo.query.get_or_404(id)  # id se record nikalta hai
    db.session.delete(todo)           # record delete karta hai
    db.session.commit()               # database me changes save karta hai
    return redirect("/")              # wapas home page par redirect
    

@app.route("/product")
def product():
    return "<h1>This is the Product Page</h1>"

# -----------------------------
# Main Entry Point
# -----------------------------
if __name__ == "__main__":
    # Delete old corrupt database if exists (optional safety)
    db_path = os.path.join(BASE_DIR, 'site.db')
    if os.path.exists(db_path):
        try:
            # Try to connect just to ensure it's valid
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check;")
            conn.close()
        except sqlite3.DatabaseError:
            print("⚠️ Old database corrupted. Deleting...")
            os.remove(db_path)

    with app.app_context():
        db.create_all()  # Create new valid database if needed

    app.run(debug=True)
