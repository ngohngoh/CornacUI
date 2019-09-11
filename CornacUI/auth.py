import os
import shutil
from flask import current_app as app
from flask import Blueprint
from flask import redirect, render_template, flash, request, session, url_for
from flask_login import login_required, logout_user, current_user, login_user, LoginManager
from forms import LoginForm, SignupForm
from flask_sqlalchemy import SQLAlchemy
from models import *

login_manager = LoginManager()

auth_bp = Blueprint('auth_bp', __name__, template_folder="templates", 
                    static_folder="static")


# LOGIN PAGE
@auth_bp.route("/", methods=["GET", "POST"])
def login():
    try:
        user = current_user.username
        return redirect(url_for('main_bp.home'))
    except:
        login_form = LoginForm(request.form)
        if request.method == "POST":
            if login_form.validate():
                username = request.form.get("username")
                password = request.form.get("password")
                user = User.query.filter_by(username=username).first()
                if user:
                    if user.check_password(password = password):
                        login_user(user)
                        next = request.args.get("next")
                        return redirect(next or url_for("main_bp.home")) 
            flash("Username/password is incorrect. Please try again!")
        return render_template("layouts/login.html", form=LoginForm())


# SIGN UP PAGE
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    try:
        user = current_user.username
        return redirect(url_for('main_bp.home'))
    except:
        signup_form = SignupForm(request.form)
        if request.method=="POST":
            if signup_form.validate():
                username = request.form.get("username")
                password = request.form.get("password")
                existing_user = User.query.filter_by(username=username).first()
                if existing_user == None:
                    user = User()
                    user = User(username=username, password=password)
                    db.session.add(user)
                    db.session.commit()
                    path = "uploads/" + user.username
                    user_results = os.path.join(path, "user_results.pkl")
                    if not os.path.exists(path):
                        os.makedirs(path)
                        open(user_results, "x")
                    login_user(user)
                    return redirect(url_for("main_bp.home"))
                else:
                    flash("Username has been taken!")
            else:
                flash("Invalid fields provided")
        return render_template("layouts/signup.html", form=SignupForm())


# PROFILE PAGE
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = current_user.username
    user = User.query.filter_by(username=username).first()
    signup_form = SignupForm(request.form)
    if request.method=="POST":
        new_password = request.form.get("password")
        confirm = request.form.get("confirm")
        if new_password == confirm:
            user.password = new_password
            db.session.commit()
            flash("Password has been changed!")
        else:
            flash("Your new password is not the same!")
    return render_template("layouts/profile.html", form=SignupForm(), user=user)

# DELETE ACCOUNT
@auth_bp.route("/remove", methods=["GET"])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    user_path = os.path.join("uploads", current_user.username)
    shutil.rmtree(user_path)
    flash("Your account has been successfully deleted!")
    return redirect(url_for("auth_bp.login"))


# LOGIN HELPERS
@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out!")
    return redirect(url_for('auth_bp.login'))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view that page.")
    return redirect(url_for('auth_bp.login'))

