# CornacUI

Cornac-UI is an user interface built on top of [Cornac](https://github.com/PreferredAI/cornac). This application will allow users to work around Cornac without having to understand how the codes run in the backend and yet still able to train their own recommendation model. 

## Installation
Before running this application, [Cornac](https://github.com/PreferredAI/cornac) has to be installed first.

### For Cornac

  - **From PyPI (you may need a C++ compiler):**

```sh
pip3 install cornac
```

  - **From Anaconda:**

```sh
conda install cornac -c conda-forge
```

  - **From the GitHub source (for latest updates):**

```sh
pip3 install Cython
git clone https://github.com/PreferredAI/cornac.git
cd cornac
python3 setup.py install
```

### For Cornac-UI
  - **From Flask:**
```sh
pip install Flask
```

## Getting started with Cornac-UI (on localhost)
1) Download the whole Cornac-UI folder into your directory
2) Open the folder on any Integrated Development Environment (e.g. Visual Studio)
3) Run the app.py file 
4) Start trying the app on the browser @ [localhost:4002](http://localhost:4002)

## Working around the UI
1) Register an account - username and password of **minimum 6 characters**
2) Hit the **"Get Started"** button to start try running some results
3) Select the model that you want to work with 
  - currently there is only 3 models: [PMF](https://github.com/PreferredAI/cornac/tree/master/cornac/models/pmf), [MF](https://github.com/PreferredAI/cornac/tree/master/cornac/models/mf) and [BPR](https://github.com/PreferredAI/cornac/tree/master/cornac/models/bpr)
  - more models will be extended to Cornac-UI in the near future 
  - **[Developer] adding in more models are relatively simple where you just have to create a HTML template for a form input parameter and also adding the relevant model function parameters into app.py**
4) By submitting the input parameters, it will take a short moment for the model to be trained (depending on your data size) and an output which looks like this:

|     |    MAE |   RMSE | Recall@20 | NDCG@20 |    AUC | Train (s) | Test (s) |
| --- | -----: | -----: | --------: | ------: | -----: | --------: | -------: |
| MF | 0.7441 | 0.9007 |    0.0622 |  0.0534 | 0.2952 |    0.0791 |   1.3119 |
| PMF | 0.7490 | 0.9093 |    0.0831 |  0.0683 | 0.4660 |    8.7645 |   2.1569 |
| BPR | N/A | N/A |    0.1449 |  0.1124 | 0.8750 |    0.8898 |   1.3769 |


## Results saved 
Cornac-UI is able to store the results of all the runs made by the users. By clicking on their username at the top right-hand tab, under results they will be able to see ALL their past run results. 

Users are able to see the parameters that they had input for each run and also, if they wish to utilise their trained model from any run, they are able to download their trained model (pickle file) to be applied in their own application. 
