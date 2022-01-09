import wtforms
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from forms import WriteNews, RegisterForm, LoginForm, CommentForm
from flask import abort
from flask_gravatar import Gravatar
from datetime import datetime
import time
import os

# date for later use
today = datetime.now()

# Only user at the top in db, only can make changes
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Creating app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

gravatar = Gravatar(app, size=100, rating="g", default="retro", force_lower=False, use_ssl=False, base_url=None)

# Database Table
class NewsPost(UserMixin, db.Model):
    __tablename__ = "news_post"
    id = db.Column(db.Integer, primary_key=True)
    # Child relationship with Users
    # refrence to primary key of parent table i.e ForeignKey
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # back reference to users obj
    author = relationship("Users", back_populates="news")

    title = db.Column(db.String(200), unique=True, nullable=False)
    subtitle = db.Column(db.String(150), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, unique=True, nullable=False)
    date = db.Column(db.String(250), nullable=False)

    # Parent relationship with Comments
    comments = relationship("Comment", back_populates="parent_news")

# db for registered Users
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True,  nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    # Parent relationship with newspost
    news = relationship("NewsPost", back_populates="author")

    # Parent relationship to Comment
    comments = relationship("Comment", back_populates="comment_user")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # Child relation with Users
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_user = relationship("Users", back_populates="comments")

    # Child relation with NewsPost
    news_id = db.Column(db.Integer, db.ForeignKey("news_post.id"))
    parent_news = relationship("NewsPost", back_populates="comments")

db.create_all()

# Routes and functions
@app.route('/')
def show_all_news():
    all_posts = db.session.query(NewsPost).all()
    return render_template("index.html", posts=all_posts, current_user=current_user)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/register', methods=["GET","POST"])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():

        if Users.query.filter_by(email=register_form.email.data).first():
            flash("User already registered. please Login.")
            time.sleep(2)
            return redirect(url_for("login"))

        hash_salted_passsword = generate_password_hash(
            password=register_form.password.data,
            method="pbkdf2:sha256",
            salt_length=8
        )

        new_user = Users(
            email=register_form.email.data,
            password=hash_salted_passsword,
            name=register_form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("show_all_news"))
    return render_template("register.html", form=register_form, current_user=current_user)

@app.route('/login', methods=["GET","POST"])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = Users.query.filter_by(email=email).first()
        if not user:
            flash("User Not Found, Please Register First.")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, password):
            flash("Password did not match! Please try again.")
        else:
            login_user(user)
            return redirect(url_for("show_all_news"))

    return render_template("login.html", form=login_form, current_user=current_user)

@app.route("/post/<int:news_id>", methods=["GET","POST"])
def read_a_news(news_id):
    form = CommentForm()
    requested_news = NewsPost.query.get(news_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Sorry, You need to login/register to comment.")
            return redirect(url_for("login"))
        new_comment = Comment(
            text=form.comment_text.data,
            comment_user=current_user,
            parent_news=requested_news
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", form=form, req_news=requested_news, current_user=current_user)

@app.route('/write-news', methods=["GET","POST"])
@admin_only
def write_news():
    news_form = WriteNews()
    if news_form.validate_on_submit():
        news = NewsPost(
            title=news_form.title.data,
            subtitle=news_form.subtitle.data,
            img_url=news_form.img_url.data,
            author=current_user,
            content=news_form.content.data,
            date=f"{today.strftime('%d')} {today.strftime('%B')} {today.year}"
        )
        db.session.add(news)
        db.session.commit()
        return redirect(url_for("show_all_news"))
    return render_template("write-news.html", form=news_form, current_user=current_user)

@app.route('/logout', methods=["GET","POST"])
def logout():
    logout_user()
    return redirect(url_for("show_all_news"))

@app.route('/delete/<int:news_id>', methods=["GET","POST"])
@login_required
@admin_only
def delete_news(news_id):
    news_to_delete = NewsPost.query.get(news_id)
    db.session.delete(news_to_delete)
    db.session.commit()
    return redirect(url_for("show_all_news"))

if __name__ == "__main__":
    app.run(debug=True)
