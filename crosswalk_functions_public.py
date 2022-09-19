import numpy as np
import pandas as pd
import sys
import os
import warnings
sys.path.append('../')
import paths as pth
import mrtool



def create_diff_variables(df, resp_name, se_name, cov_name, suffixes=('_sens', '_ref')):
    df[resp_name + '_diff'] = df[resp_name + suffixes[0]] - df[resp_name + suffixes[1]]
    df[se_name + '_diff'] = np.sqrt(df[se_name + suffixes[0]]**2 + df[se_name + suffixes[1]]**2)
    df[cov_name + '_diff'] = df[cov_name + suffixes[0]] - df[cov_name + suffixes[1]]
    
    return df


def cwalk(df, resp_name, se_name, cov_name, study_id, monotonicity=None):

    cwd = mrtool.MRData(obs=df[resp_name + '_diff'].to_numpy(),
                        obs_se=df[se_name + '_diff'].to_numpy(),
                        covs={cov_name + '_diff': df[cov_name + '_diff'].to_numpy()},
                        study_id=df[study_id].to_numpy(),
                        data_id=df.index.to_numpy()
            )
    if monotonicity is not None:
        if monotonicity == 'increasing':
             prior_beta_uniform = np.array([0.0, np.inf])
        elif monotonicity == 'decreasing':
            prior_beta_uniform = np.array([-np.inf, 0.0])
    else:
        prior_beta_uniform = None

    mr = mrtool.MRBRT(data=cwd,
                      cov_models=[
                          mrtool.LinearCovModel('intercept', use_re=False,
                                                prior_beta_uniform=np.array([0.0, 0.0])),
                          mrtool.LinearCovModel(alt_cov=cov_name + '_diff', use_re=False,
                                                prior_beta_uniform=prior_beta_uniform)]
            )
    mr.fit_model(inner_max_iter=1000, outer_max_iter=2000)

    return mr

def cwalk_multivar(df, resp_name, se_name, cov_names, study_id, monotonicity=None):

    cov_diff_names = [v + '_diff' for v in cov_names]
    cwd = mrtool.MRData(obs=df[resp_name + '_diff'].to_numpy(),
                        obs_se=df[se_name + '_diff'].to_numpy(),
                        covs={cov_name: df[cov_name].to_numpy() for cov_name in cov_diff_names},
                        study_id=df[study_id].to_numpy(),
                        data_id=df.index.to_numpy()
            )
    prior_beta_uniform = {'intercept': np.array([0.0, 0.0])}
    if monotonicity is not None:
        for cov_name, monot in monotonicity.items():
            if monot == 'increasing':
                prior_beta_uniform.update({cov_name + '_diff': np.array([0.0, np.inf])})
            elif monot == 'decreasing':
                prior_beta_uniform.update({cov_name + '_diff': np.array([-np.inf, 0.0])})

    mr = mrtool.MRBRT(data=cwd,
                      cov_models=[
                          mrtool.LinearCovModel(cov_name, use_re=False,
                                                prior_beta_uniform=prior_beta_uniform.get(cov_name))\
                                                        for cov_name in ['intercept'] + cov_diff_names])
    mr.fit_model(inner_max_iter=1000, outer_max_iter=2000)

    return mr

def summarize_cwalk(mr, cov_name, n_samples=1000, seed=24601):
    beta_samples, _ = mr.sample_soln(sample_size=n_samples)
    if type(cov_name) == str:
        cov_names = [cov_name]
    elif type(cov_name) == list:
        cov_names = cov_name
    par_summary = pd.DataFrame({'beta': mr.beta_soln[1:],
                                'se_beta': beta_samples[:, 1:].std(axis=0),
                                'sample_size': np.full((len(cov_names)), mr.data.obs.shape[0])},
                               index=[cov_name])
    return (beta_samples[:, 1:],
            par_summary)

def compare_sd_versions(mr, beta_samples=None, n_samples=1000, seed=24601):
    if beta_samples is None:
        beta_samples, _ = mr.sample_soln(sample_size=n_samples)
        beta_samples = beta_samples[:, 1]

    lme_specs = mrtool.core.other_sampling.extract_simple_lme_specs(mr)
    hessn = mrtool.core.other_sampling.extract_simple_lme_hessian(lme_specs)
    sigma = np.linalg.inv(hessn)

    f_info_se = np.sqrt(sigma[1, 1] - (sigma[0, 1]**2 / sigma[0, 0]))
    resample_se = beta_samples.std()

    return {'Fisher Information': f_info_se,
            'Fit-Refit': resample_se}

