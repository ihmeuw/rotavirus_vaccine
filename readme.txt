# Cost Effectiveness Meta Regression of Rotavirus Vaccination
This repository contains the code that performs the cost effectiveness 
meta-regression analysis of Rotavirus vaccination programs. This analysis 
has been accepted for publication in Vaccine under the title, 
"Cost-effectiveness of Rotavirus vaccination in children under five years 
of age in 195 Countries: A Metaregression Analysis".

## Purpose
The purpose for this repository is to make the analytic code for this 
project available as part of [Guidelines for Accurate and Transparent 
Health Estimates Reporting (GATHER)](http://gather-statement.org/) 
compliance.

## Organization
All input, intermediate, and output files are defined in the file 
paths.py, and are replaced with "FILEPATH".

Scripts should be run in the following order:

1. create_prediction_df_public.py

   Constructs a data set consisting of pairs of ratios from the same 
article and location that differ only in that they use different values of 
one covariate.

2. crosswalks_public.ipynb

   Analyses of differences between ICERs for sensitivity-reference pairs 
of ratios. Uses functions defined in crosswalk_functions.py.

3. rotavirus_mr_public.ipynb

   Most of the analytic code as well as some code to generate plots, 
including those in Figure 2 of the publication. Uses functions defined in 
mr_functions.py and plotting_functions.py.

4. create_prediction_df_public.py

   Generates predictions and uncertainty intervals using model objects 
fitted in hpv_analysis.py.

5. The logistics regression code file is unavailable. It is possible to 
reference the logistic_regression.R from 
https://github.com/ihmeuw/cost_effectiveness_hpv_vax_metareg for a 
comparable analysis. 

6. Code to map the ICERs is currently unavailable. It is possible to 
reference the map_icers.R from 
https://github.com/ihmeuw/cost_effectiveness_hpv_vax_metareg for a 
comparable analysis. 

## Inputs
Inputs required for the code to run are:

1. Valid paths to directories must be specified as ROOT_DIR, PLOT_DIR, and 
MODEL_RESULTS_DIR in paths.py.

2. A data file whose path is specified in paths.py as CLEANED_REG_DF.

3. A file specifying the values of all covariates for each prediction. Its 
path is specified in paths.py as CLEANED_PREDS_DF.

4. A shapefile in rds format that defines the boundaries of countries. 
This is used only in map_icers.R and is saved in a location specified as 
SHAPEFILE in paths.py.
