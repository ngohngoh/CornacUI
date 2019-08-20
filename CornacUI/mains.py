import os 
import cornac 
import pickle 
                        
from flask import Blueprint, render_template
from flask import request, jsonify, send_from_directory
from flask_login import current_user
from flask import current_app as app
from flask_login import login_required

from cornac.utils import cache

from functions import upload, allowed_file, user_input, read_data, \
                        select_eval, select_metrics, select_model,  \
                        check_folder

hello = "yi long"
main_bp = Blueprint('main_bp', __name__, template_folder="templates", 
                    static_folder="static")


import redis
from rq import Queue
r = redis.Redis()
q = Queue(connection=r)


def background_task():
    print("Working on task now!")
    return 1



# HOME PAGE
@main_bp.route('/home', methods=["GET"])
@login_required
def home():
    # all_users = User.query.all()
    # print(all_users)
    # user = User.query.filter_by(username="").first()
    # print(user.password)
    return render_template("layouts/home.html")

# USER PAGE
@main_bp.route('/train/<parameter>', methods=["GET", "POST"])
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

        job = q.enqueue(background_task)
        # print(f"Task ({job.id}) added to queue at {job.enqueued_at}")
        print("Task: ", job.id, job.enqueued_at)

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

# USER RESULTS
@main_bp.route("/results", methods=["GET"])
@login_required
def past_results():
    user = current_user.username
    fpath = os.path.join("uploads", user, "user_results.pkl")
    try: 
        user_results = pickle.load(open(fpath, "rb"))
        return render_template("layouts/results.html", user_results=user_results)        
    except:
        return render_template("layouts/results.html")

# DOWNLOAD TRAINED MODEL
@main_bp.route("/download/<run>", methods=["GET", "POST"])
@login_required
def download(run):
    user = current_user.username
    model_dir = os.path.join("uploads", user, run)
    model_file = "trained_model.pkl"
    return send_from_directory(model_dir, model_file, as_attachment = True)