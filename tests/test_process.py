from sivnorm.process import fuzzymatch, cleaning, wrap_cleaning, wrap_fuzzymatch, df_marque_modele

import pandas as pd
from multiprocessing import Pool
import time
def test_process():
    row = dict(modele='renault clio',marque='renault')
    res = fuzzymatch(cleaning(row))
    assert res == {"marque": "RENAULT", "modele": "CLIO", "score":1}, res
    row = dict(modele='',marque='renault')
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned)
    assert res == {"marque": "RENAULT", "modele": "", "score":0.5}, res



data = [['renault','clio'],
        ['renault','clio2'],
        ['renault','renault clio7'],
        ['renault','clio7 RT/RN'],
        ['renault','clio 5portes turbo'],
        ['renault','cli o'],
        ['renault','clino'],
        ['reneaut','reneaud clioRT']]

df_small = pd.DataFrame(columns=['marque','modele'],data=data)

df_large = pd.DataFrame(columns=['marque','modele'], data=int(1e2)*[['renault','clio']])
df_large = pd.concat([df_large, df_small], ignore_index=True)

def process_df(df):
    workers = 10
    t1 = time.time()
    pool = Pool(workers)
    res = pool.map(wrap_cleaning, df.iterrows())
    df_res = pd.DataFrame(res)
    sec_wl = (workers*(time.time() - t1))/(df.shape[0])
    print( "%.2f seconds per worker per line" % sec_wl )

    assert (df_res['marque'] == 'RENAULT').all(), df_res['marque'].unique()
    assert (df_res['modele'] == 'CLIO').all(), df_res['modele'].unique()
    assert df.shape[0] == df_res.shape[0], 'different shape'

    pool.close()

def process_df_fast(df):

    workers = 10
    t1 = time.time()




    pool = Pool(workers)
    res = pool.map(wrap_cleaning, df.iterrows())
    df_clean = pd.DataFrame(res)
    filter = (df_clean['marque'].isin(df_marque_modele['marque'])) &\
             (df_clean['modele'].isin(df_marque_modele['modele']))

    df_diff = df_clean[~filter]
    print(df_diff.shape[0])
    print(df_diff.tail())
    pool.close()

    pool = Pool(workers)
    res = pool.map(wrap_fuzzymatch, df_diff.iterrows())
    df_res = pd.DataFrame(res)

    df_res = pd.concat([df_res, df_clean[filter]], ignore_index=False)
    print(df_res.tail(15))

    sec_wl = (workers*(time.time() - t1))/(df.shape[0])
    print( "%.2f seconds per worker per line" % sec_wl )

    assert (df_res['marque'] == 'RENAULT').all(), df_res['marque'].unique()
    assert (df_res['modele'] == 'CLIO').all(), df_res['modele'].unique()
    assert df.shape[0] == df_res.shape[0], 'different shape, %d != %d'%(df.shape[0], df_res.shape[0])

    pool.close()

def test_process_df():
    for df in [df_small, df_large]:
        process_df(df)


if __name__ == '__main__':
    process_df_fast(df_large)
