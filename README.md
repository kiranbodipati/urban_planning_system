# U.P.S.E.T
## Urban Planning System for Enhancement of Transport

The Singapore public transport network is certainly one of the best in the world - it is densely connected, reaches most regions of the island and provides a clean, punctual, and significantly cheaper alternative to private transportation and cabs. However, it is far from perfect - in 2018, average commute time to/from work was found to be 84 minutes, and has since improved to 46 minutes in 2021. Clearly, there was significant margin for improvement back then, and we still believe from personal experience that increasing frequencies of certain bus routes could massively decrease travel time. 
Official statistics state that the current average waiting time is still around 8 minutes. Our hypothesis was that reinforcing existing bottlenecked bus routes with higher frequencies or adding new connections in certain unconnected areas could reduce this time, and our aim was to find which routes should be the first targets for such corrective action for efficient allocation of resources.


### Installation

Install dependencies using the `requirements.txt` file. We recommend using a virtual environment with `python>=3.9.0` for smooth execution. 

```
pip install -r requirements.txt 
```

### Streamlit App

The Streamlit app contains the source for the final dashboard of the product. The files can be found in the `app` directory. The data files present in the `data` and `results` directories follows relative path, so the folder structure needs to be preserved. 

```
urban_planning_system
│   README.md
│   ** analysis ipynb notebooks **
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

### Notebooks, Data and Results

The various notebooks used for data cleaning, pre-processing and analysis can be found in the root folder. The processed data files are found in the `data` folder, and the inferences and model weights can be found in the `results` folder. All the graph networks are stored in a neo4j database, and are fetched by the app on api calls. There are two more data files from the LTA data mall that are too large to be directly included in this repository, and can be found at {insert links here}

