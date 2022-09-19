import numpy as np
import pandas as pd
import sys
import os
import warnings
sys.path(FILEPATH)
import paths as pth
from db_queries import get_population, get_outputs,\
    get_location_metadata, get_covariate_estimates

costs_df = pd.read_csv(pth.CONV_PRED_VACC_COSTS)
lmtdta = get_location_metadata(location_set_id=35, gbd_round_id=5)
lmtdta.loc[lmtdta['level'] == 3, ['location_id', 'location_name']]
locns = list(costs_df['location_id'].unique())
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dalys = get_outputs('rei', gbd_round_id=5, location_id=locns,
                        year_id=2017, sex_id=3, age_group_id=[1, 6],
                        cause_id=302, rei_id=181, measure_id=2)
pops = get_population(location_id=locns, year_id=2017,
                      age_group_id=[1, 6], gbd_round_id=5, sex_id=3)

dalys = dalys[['location_id', 'age_group_id', 'val']]
pops = pops[['location_id', 'age_group_id', 'population']]
dalys = dalys.merge(pops, on=['location_id', 'age_group_id'])

agg_dalys = dalys.groupby('location_id')[['val', 'population']].sum().reset_index()
agg_dalys['age_group_id'] = '1,6'
dalys['age_group_id'] = dalys['age_group_id'].astype(str)
dalys = pd.concat([dalys, agg_dalys], axis=0, ignore_index=True)

dalys['burden_variable'] = dalys['val'] / dalys['population']

dalys = dalys.drop(['val', 'population'], axis=1)
dalys = dalys[dalys['age_group_id'] == '1']

df = costs_df.merge(dalys, on='location_id')

gdp_df = pd.read_csv(pth.GDP_DF)
gdp_df = gdp_df.loc[gdp_df['year'] == 2017,
                    ['location_id', 'ihme_loc_id',
                    'GDP_2017usd_per_cap', 'GDP_2017ppp_per_cap']
                   ].reset_index(drop=True)
df = df.merge(gdp_df, on=['location_id', 'ihme_loc_id'])

vars_to_log = ['burden_variable', 'GDP_2017ppp_per_cap', 'GDP_2017usd_per_cap']
df = df.assign(**{'log_' + k: np.log(df[k]) for k in vars_to_log})

dtp_coverage = get_covariate_estimates(covariate_id=32, year_id=2017, sex_id=3,
                                       location_id=locns, gbd_round_id=5, age_group_id=22)
dtp_coverage = dtp_coverage[['location_id', 'mean_value']]
dtp_coverage = dtp_coverage.rename({'mean_value': 'dtp3_coverage'}, axis=1)
df = df.merge(dtp_coverage, on='location_id')

efficacy = pd.read_csv(pth.PRED_VACC_EFFICACY)
efficacy = efficacy[efficacy['year_id'] == 2017]
efficacy = efficacy.rename({'pred_ve': 'efficacy'}, axis=1)

# UK is missing from efficacy csv, but subnationals are present.
# Take pop. weighted average of England, Scotland, Wales, & NI
subntl_effs = efficacy.merge(lmtdta[['location_id', 'level', 'parent_id']], on='location_id')
subntl_effs = subntl_effs.loc[subntl_effs['level'] == 4].reset_index(drop=True)

subntl_pops = get_population(gbd_round_id=5, location_id=list(subntl_effs['location_id'].unique()),
                             age_group_id=22, year_id=2017, sex_id=3)
subntl_pops = subntl_pops.groupby('location_id')['population'].sum().reset_index()

subntl_effs = subntl_effs.merge(subntl_pops[['location_id', 'population']], on='location_id')
subntl_effs['eff_x_pop'] = subntl_effs['efficacy'] * subntl_effs['population']
subntl_effs = subntl_effs.groupby('parent_id')[['eff_x_pop', 'population']].sum().reset_index()
subntl_effs['efficacy'] = subntl_effs['eff_x_pop'] / subntl_effs['population']
subntl_effs = subntl_effs.rename({'parent_id': 'location_id'}, axis=1)

subntl_effs = subntl_effs.merge(lmtdta[['location_id', 'location_name']], on='location_id')
subntl_effs = subntl_effs.loc[~subntl_effs['location_id'].isin(efficacy['location_id'].unique())]
subntl_effs['year_id'] = 2017
subntl_effs['pred_se'] = np.nan
subntl_effs = subntl_effs.drop(['eff_x_pop', 'population'], axis=1)
efficacy = pd.concat([efficacy, subntl_effs], axis=0, ignore_index=True)


df = df.merge(efficacy[['location_id', 'efficacy']], on='location_id')
# Efficacy on percent scale 
df['efficacy'] = df['efficacy'] * 100

cov_default_dict = {'intercept': 1,
                    'pentavalent': 0,
                    'both_types': 0,
                    'payer': 1,
                    'CostsDiscountRate': 3,
                    'DiscountRate': 3,
                    'coverage': 90,
                    'qalys': 0,
                    'not_lifetime': 0,
                    'ltd_societal': 0,
                    'ltd_and_societal': 0,
                    'sector': 0
                    }
df = df.assign(**{k: v for k, v in cov_default_dict.items()})
if not os.path.exists(pth.PREDS_DF):
    df.to_csv(pth.PREDS_DF, index=False)
    print('Wrote preds df to ' + pth.PREDS_DF)
else:
    print('Output path already exists.')