# U.P.S.E.T
## Urban Planning System for Enhancement of Transport
*****


#### Installation

Install dependencies using the `requirements.txt` file. We recommend using a virtual environment with `python>=3.9.0` for smooth execution. 

```
pip install -r requirements.txt 
```

#### Streamlit App

The Streamlit app contains the source for the final dashboard of the product. The files can be found in the `app` directory. The data files present in the `data` and `results` directories follows relative path, so the folder structure needs to be preserved. 

```
urban_planning_system
│   README.md
│
└───app
│   │   Home.py
│   │   bus.gif
│   │   mrt.gif
|   |───helpers
│   |   │   helpers.py
│   └───pages
│       │   1_Bus_Analysis.py
│       │   2_MRT_Analysis.py
│       │   3_Suggested_Improvements.py
│   
└───data
└───results

```

To execute the app, navigate to the `app` folder and execute `Home.py`.

```
cd app
streamlit run Home.py
```

