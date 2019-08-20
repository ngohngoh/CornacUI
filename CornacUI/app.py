import os
import shutil
import cornac
import pickle

from flask import Flask, flash, render_template, session
from flask import redirect, request, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, logout_user, current_user, login_user

from cornac.datasets import movielens
from cornac.eval_methods import RatioSplit, CrossValidation
from cornac.models import PMF, MF, BPR
from cornac.data import Reader
from cornac.utils import cache, validate_format

########## FLASK APP SETTINGS ##########
app = Flask(__name__)
app.config.from_object(__name__)
app._static_folder = os.path.abspath("static/")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accounts.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.urandom(12).hex()

########## LOGIN/DB SETTINGS ##########
db = SQLAlchemy(app)
login_manager = LoginManager(app)

from flask_login import UserMixin
# from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer,
                    primary_key=True)
    username = db.Column(db.String(20),
                    nullable=False,
                    unique=True)
    password = db.Column(db.String(20),
                    nullable=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        # return check_password_hash(self.password, password) 
        return self.password==password

    def __repr__(self):
        return "<User %r>" % (self.username)

########## FLASK APP FUNCTIONS ##########

# CHECKING FOR FILE EXTENSION
ALLOWED_EXTENSIONS = set(['txt', 'csv'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# UPLOADING OF DATA 
def upload(upload_files):
    file_types = list(upload_files.keys())
    for file_type in file_types:
        file = request.files[file_type]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_type, filename))
        else:
            return False
    return True

# STORING OF INPUT PARAMETER (DICT)
def user_input(user_form, user_files):
    inputParam = {}
    for name, parameter in user_form.items():
        if name == "metrics":
            inputParam["metrics"] = user_form.getlist("metrics")
            print("input metrics:", inputParam["metrics"])
        else:
            inputParam[name] = parameter
    user_filenames = list(user_files.values())
    inputParam["data_file"] = secure_filename(user_filenames[0].filename)
    # inputParam["meta_file"] = secure_filename(user_filenames[1].filename)
    
    return inputParam

# READING DATASET
def read_data(path):
    fmt = validate_format("UIR", ["UIR", "UIRT"]) # HARDCODE UIR 
    reader = None
    reader = Reader() if reader is None else reader
    data = reader.read(path)

    return data

# READING METADATA 
def read_meta(path):
    data = {}
    with open(path) as f:
        for row in f:
            content = row.strip().split('|')
            id = content[0]   # item id 
            name = content[1] # item name
            data[id] = name
    return data

# SELECTING OF EVALUATION METHODS
def select_eval(method, dataset):
    if method == "ratio_split":
        return RatioSplit(data=dataset, test_size=0.2, 
                        rating_threshold=4.0, exclude_unknowns=False)
    elif method == "cross_validation":
        return CrossValidation(data=dataset, rating_threshold=1.0, exclude_unknowns=False)

# SELECTING OF MODELS
def select_model(user_input):
    if user_input["model"] == "pmf":
        model_selected = PMF(k=int(user_input["lf"]), max_iter=int(user_input["iteration"]), 
                learning_rate=float(user_input["lr"]), lamda=float(user_input["rp"]), 
                variant=user_input["variant"], verbose=True)
    elif user_input["model"] == "mf":
        model_selected = MF(k=int(user_input["lf"]), max_iter=int(user_input["iteration"]), 
                learning_rate=float(user_input["lr"]), lambda_reg=float(user_input["rp"]), 
                use_bias=True)
    elif user_input["model"] == "bpr":
        model_selected = BPR(k=int(user_input["lf"]), max_iter=int(user_input["iteration"]), 
                learning_rate=float(user_input["lr"]), lambda_reg=float(user_input["rp"]), verbose=True)
    return model_selected 

# SELECTING OF METRICS
def select_metrics(metrics, inputParam):
    metrics_chosen = []
    for metric in metrics:
        if metric == "mae":
            metrics_chosen.append(cornac.metrics.MAE())
        elif metric == "rmse":
            metrics_chosen.append(cornac.metrics.RMSE())
        elif metric == "recall":
            metrics_chosen.append(cornac.metrics.Recall(k=int(inputParam["recall_val"])))
        elif metric == "precision":
            metrics_chosen.append(cornac.metrics.Precision(k=int(inputParam["precision_val"])))
    return metrics_chosen


# CHECKING OF FOLDER EXISTENCE
def check_folder(path):
    runs = os.listdir(path)
    print("runs:", runs)
    if len(runs) == 1:
        return 1
    
    runs.remove("user_results.pkl") 
    num = [int(run) for run in runs]
    return max(num) + 1

########### CLASSES ###########

from wtforms import Form, StringField, PasswordField, validators, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional, InputRequired

class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired(message=("Please enter your username"))])
    password = PasswordField("Password", validators=[DataRequired(message=("Please enter your password"))])
    login = SubmitField("Log In")

class SignupForm(Form):
    username = StringField("Username", validators=[InputRequired(message=("Please enter a username")),
                                                Length(min=6, message=("Your username must be at least 6 characters"))])
    password = PasswordField("Password", validators=[DataRequired(message=("Please enter your password")),
                                                Length(min=6, message=("Your password must be at least 6 characters"))])
    confirm = PasswordField("Confirm Your Password", validators=[DataRequired(), EqualTo("password", message=("Passwords do not match"))])
    signup = SubmitField("Sign Up")

########### FLASK APP ROUTING ###########

# PROFILE PAGE
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = current_user.username
    user = User.query.filter_by(username=username).first()
    signup_form = SignupForm(request.form)
    if request.method=="POST":
        new_password = request.form.get("password")
        confirm = request.form.get("confirm")
        if new_password == confirm:
            print("changing password")
            user.password = new_password
            db.session.commit()
            flash("Password has been changed!")
    return render_template("layouts/profile.html", form=SignupForm(), user=user)

# DOWNLOAD TRAINED MODEL
@app.route("/download/<run>", methods=["GET", "POST"])
@login_required
def download(run):
    user = current_user.username
    model_dir = os.path.join("uploads", user, run)
    model_file = "trained_model.pkl"
    return send_from_directory(model_dir, model_file, as_attachment = True)

# SIGN UP PAGE
@app.route("/signup", methods=["GET", "POST"])
def signup():
    signup_form = SignupForm(request.form)
    if request.method=="POST":
        if signup_form.validate():
            print("Validating...")
            username = request.form.get("username")
            password = request.form.get("password")
            existing_user = User.query.filter_by(username=username).first()
            if existing_user == None:
                user = User()
                user = User(username=username, password=password)
                db.session.add(user)
                db.session.commit()
                print("new user added")
                path = "uploads/" + user.username
                user_results = os.path.join(path, "user_results.pkl")
                if not os.path.exists(path):
                    print("created db")
                    os.makedirs(path)
                    open(user_results, "x")
                login_user(user)
                return redirect(url_for("main_bp.home"))
            else:
                flash("Username has been taken!")
        else:
            flash("Invalid fields provided")
    return render_template("layouts/signup.html", form=SignupForm())

# LOGIN PAGE
@app.route("/", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if request.method == "POST":
        if login_form.validate():
            print("checking")
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            if user:
                print("checking password")
                if user.check_password(password = password):
                    login_user(user)
                    print("Logging in...")
                    next = request.args.get("next")
                    print("next:", next)
                    return redirect(next or url_for("main_bp.home")) 
        flash("Username/password is incorrect. Please try again!")
    return render_template("layouts/login.html", form=LoginForm())

# DELETE ACCOUNT
@app.route("/remove", methods=["GET"])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    user_path = os.path.join("uploads", current_user.username)
    shutil.rmtree(user_path)
    flash("Your account has been successfully deleted!")
    return redirect(url_for("auth_bp.login"))

# HOME PAGE
@app.route('/home', methods=["GET"])
@login_required
def home():
    # all_users = User.query.all()
    # print(all_users)
    # user = User.query.filter_by(username="").first()
    # print(user.password)
    return render_template("layouts/home.html")


# USER PAGE (TEST)
# @app.route("/train/", methods=["GET", "POST"])
# @login_required
# def training():
#     if request.method == "GET":


# USER PAGE
@app.route('/train/<parameter>', methods=["GET", "POST"])
@login_required
def run_model(parameter):
    # Parameter here is the model's acronym sent in the link
    if request.method == "GET":
        return render_template("models/{}.html".format(parameter), display=parameter)

    else: 
        form_files = request.files
        print("form files:", form_files)
        form_data = request.form
        print("form data:", form_data)

        errors = []

        # IF metrics not checked
        if "metrics" not in form_data:
            errors.append("Please check at least one or more metrics")
        # IF files are not uploaded 
        if len(form_files) == 0:
            errors.append("Please ensure the dataset file is uploaded")
        # IF file extension error
        elif not upload(form_files):
            errors.append("Upload was unsuccessful")
            errors.append("Accepted file types: .txt, .csv")

        if len(errors) > 0: 
            return jsonify({"errors": errors})

        inputParam = user_input(form_data, form_files)
        print("inputParam:", inputParam)

        # Reading of Dataset and Metadata
        pathData = cache(url = os.path.abspath("uploads/dataset/" + inputParam['data_file']))
        # pathMeta = cache(url = os.path.abspath("uploads/metadata/" + inputParam["meta_file"]))
        dataset = read_data(pathData)
        # metadata = read_meta(pathMeta)

        # Using Cornac
        eval_method = select_eval(inputParam["evalmethod"], dataset)
        model = select_model(inputParam)
        metrics = select_metrics(inputParam["metrics"], inputParam)

        exp10 = cornac.Experiment(eval_method=eval_method,
                                models=[model],
                                metrics=metrics,
                                user_based=True)
        # print(exp10.run())
        result = exp10.run().split("\n")
        
        # Splitting the output 
        output = []
        for line in result[1:-1]:
            if '|' in line:
                store = []
                for data in line.split('|'):
                    store.append(data)
                output.append(store)

        # Creating the run folder
        user_folder = "uploads/" + current_user.username
        current_run = check_folder(user_folder)
        run_folder = os.path.join(user_folder, str(current_run))
        os.makedirs(run_folder)

        # Saving the trained model
        model_file = "trained_model.pkl"
        model_path = os.path.join(run_folder, model_file)
        pickle.dump(model, open(model_path, "wb"))

        # Saving the run results
        results_path = user_folder + "/user_results.pkl"
        run_result = {}     
        run_result["parameter"] = inputParam
        run_result["output"] = output
        result_dict = {current_run: run_result}

        if os.stat(results_path).st_size > 0: # Old user
            print("this user has run models before")
            user_results = pickle.load(open(results_path, "rb")) 
            user_results.update(result_dict)
            pickle.dump(user_results, open(results_path, "wb"))  
        else:                                 # New user
            print("this user is new")
            pickle.dump(result_dict, open(results_path, "wb"))        

        return jsonify({"output": output, "current_run": current_run})

# # USER RECOMMENDATION 
# @app.route('/recommendations', methods=["POST"])
# def user_recommendation():
#     if request.method == "POST":
#         print("its a POST")
#         # print("session id:", session.sid)

#         reco_data = request.form
#         current_run = reco_data["current_run"]
#         uid = reco_data["user"]
#         print(current_run, uid)

#         upload_dir = os.path.join("uploads", current_user.username, current_run)
#         user_runs = os.path.join("uploads", current_user.username, "user_runs.pkl")
#         model = pickle.load(open(upload_dir + "/trained_model.pkl", "rb"))
#         past_result = pickle.load(open(user_runs, "rb"))
#         print(past_result)

#         mapped_uid = model.train_set.uid_map[uid] # getting mapped_id 
#         raw_iid = model.train_set.raw_iid_list # list of raw_iid
#         item_rank, scores = model.rank(mapped_uid) # ([mapped_iids], [scores])

#         print("ranking:", item_rank)
#         print("scores:", scores) 
#         return jsonify({"ranking": item_rank.tolist(), "scores": scores.tolist()}) 

# USER RESULTS
@app.route("/results", methods=["GET"])
@login_required
def past_results():
    user = current_user.username
    fpath = os.path.join("uploads", user, "user_results.pkl")
    try: 
        user_results = pickle.load(open(fpath, "rb"))
        return render_template("layouts/results.html", user_results=user_results)        
    except:
        return render_template("layouts/results.html")


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out!")
    return redirect(url_for('auth_bp.login'))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view that page.")
    return redirect(url_for('auth_bp.login'))

########### APP START ###########
if __name__ == '__main__':
    # sess.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    db.create_all()

    print('################### Restarting ###################')
    app.run(host='0.0.0.0', port=4002, debug=True, use_reloader=True)