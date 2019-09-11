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

main_bp = Blueprint('main_bp', __name__, template_folder="templates", 
                    static_folder="static")

from rq import Queue
from rq.job import Job
from worker import conn

q = Queue(connection=conn)

def run_task(task_input):

    inputParam, username, current_run = task_input
    user_folder = "uploads/" + username
    run_folder = os.path.join(user_folder, str(current_run))

    try: 
        # Reading of Dataset and Metadata
        pathData = os.path.abspath("uploads/dataset/" + inputParam['data_file'])
        dataset = read_data(pathData)
        # pathMeta = cache(url = os.path.abspath("uploads/metadata/" + inputParam["meta_file"]))
        # metadata = read_meta(pathMeta)

        # Using Cornac
        eval_method = select_eval(inputParam["evalmethod"], dataset)
        model = select_model(inputParam)
        metrics = select_metrics(inputParam["metrics"], inputParam)

        exp = cornac.Experiment(eval_method=eval_method,
                                models=[model],
                                metrics=metrics,
                                user_based=True)
        exp.run()
        exp_result = str(exp.result)
        result = exp_result.split("\n")

        # Splitting the output 
        output = []
        for line in result:
            if '|' in line:
                store = []
                for data in line.split('|'):
                    store.append(data)
                output.append(store)

        # Creating the run folder
        os.makedirs(run_folder)

        # Saving the trained model
        model_file = "trained_model.pkl"
        model_path = os.path.join(run_folder, model_file)
        f = open(model_path, "wb")
        pickle.dump(model, f)
        f.close()

        # Saving the run results
        results_path = user_folder + "/user_results.pkl"
        run_result = {}     
        run_result["parameter"] = inputParam
        run_result["output"] = output
        result_dict = {current_run: run_result}

        f = open(results_path, "rb")
        user_results = pickle.load(f) 
        user_results.update(result_dict)
        f.close() 

        f = open(results_path, "wb")
        pickle.dump(user_results, f)  
        f.close()   

        print("Task completed!") 

    except:
        results_path = user_folder + "/user_results.pkl"   
        result_dict = {current_run: "Training error! Try again..."}
        f = open(results_path, "rb")
        user_results = pickle.load(f) 
        user_results.update(result_dict)
        f.close() 

        f = open(results_path, "wb")
        pickle.dump(user_results, f)  
        f.close()  

        print("Training Error!")


# HOME PAGE
@main_bp.route('/home', methods=["GET"])
@login_required
def home():
    return render_template("layouts/home.html")

# USER PAGE
@main_bp.route('/train/<parameter>', methods=["GET", "POST"])
@login_required
def run_model(parameter):
    # Parameter here is the model's acronym sent in the link
    if request.method == "GET":
        return render_template("models/{}.html".format(parameter), display=parameter)

    else: 
        user = current_user.username
        form_files = request.files
        form_data = request.form

        inputParam = user_input(form_data, form_files)

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


        user_folder = "uploads/" + user
        current_run = check_folder(user_folder)

        results_path = user_folder + "/user_results.pkl"
        result_dict = {current_run: "model training in queue..."}

        if os.stat(results_path).st_size > 0: # Old user
            f = open(results_path, "rb")
            user_results = pickle.load(f) 
            user_results.update(result_dict)
            f.close() 

            f = open(results_path, "wb")
            pickle.dump(user_results, f)  
            f.close()
        else:                                 # New user
            f = open(results_path, "wb")
            pickle.dump(result_dict, f)   
            f.close() 


        # Adding Cornac task into Redis Queue
        task_input = (inputParam, user, current_run)
        job = q.enqueue(run_task, task_input)        

        return jsonify({"result": "Task has been submitted to our server..."})



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