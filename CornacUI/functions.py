import os
import cornac 

from cornac.eval_methods import RatioSplit, CrossValidation
from cornac.models import PMF, MF, BPR
from cornac.data import Reader
from cornac.utils import validate_format

from flask import request
from flask import current_app as app
from werkzeug.utils import secure_filename

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