from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

class WriteNews(FlaskForm):
    title = StringField("News Title", validators=[DataRequired()])
    subtitle = StringField("News Subtitle", validators=[DataRequired()])
    img_url = StringField("Image Url", validators=[DataRequired(), URL()])
    content = CKEditorField("News Content", validators=[DataRequired()])
    submit = SubmitField("Submit")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register Me")

class LoginForm(FlaskForm):
    email = StringField("Registered Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Post Comment")