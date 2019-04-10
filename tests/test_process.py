from sivnorm.process import fuzzymatch, cleaning, wrap_cleaning, wrap_fuzzymatch, df_cleaning, df_fuzzymatch,     ref_marque_modele

import pandas as pd
from multiprocessing import Pool
import time



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


def test_process():
    row = dict(modele='renault clio',marque='renault')
    res = fuzzymatch(cleaning(row))
    assert res == {"marque": "RENAULT", "modele": "CLIO", "score":1}, res
    row = dict(modele='',marque='renault')
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned)
    assert res == {"marque": "RENAULT", "modele": "", "score":0.5}, res

def process_df_fast(df):

    workers = 10
    t1 = time.time()


    df = df_cleaning(df, workers)

    df_res = df_fuzzymatch(df, workers)
    sec_wl = (workers*(time.time() - t1))/(df.shape[0])

    print( "%.2f seconds per worker per line" % sec_wl )

    return df_res
 
def test_process_df():
    for df in [df_small, df_large]:
        df_res = process_df_fast(df)
    assert (df_res['marque'] == 'RENAULT').all(), df_res['marque'].unique()
    assert (df_res['modele'] == 'CLIO').all(), df_res['modele'].unique()
    assert df.shape[0] == df_res.shape[0], 'different shape, %d != %d'%(df.shape[0], df_res.shape[0])


def test_app():
    import requests
    from io import StringIO

    f = StringIO()

    df_small.to_csv(f, encoding='utf-8', index=False, header= False)
  
    files = {'file': ('file.csv', f.getvalue() )}
    f.close()

    url = 'http://localhost:5000/norm'
    r = requests.post(url, files=files) 
    print(r.text)

'''

def process_df(df):
    workers = 10
    t1 = time.time()
    pool = Pool(workers)
    res = pool.map(wrap_cleaning, df.iterrows())
    pool.close()

    df_res = pd.DataFrame(res)
    sec_wl = (workers*(time.time() - t1))/(df.shape[0])

    print( "%.2f seconds per worker per line" % sec_wl )


    return df_res


'''

if __name__ == '__main__':
    test_app()
    #process_df_fast(df_large)
