import json
import re
from fuzzywuzzy import process, fuzz
from unidecode import unidecode
import pandas as pd

from multiprocessing import Pool


# dict_siv = pd.read_csv('/dss/esiv_by_cnit_python.csv').set_index('cnit_tvv').to_dict('index')
ref_marque_modele = pd.read_csv('/dss/esiv_marque_modele_genre.csv')


replace_regex = {
    'marque': {
        'BW|B\.M\.W\.|B\.M\.W|BMW I': 'BMW',
        'FIAT\.': 'FIAT',
        'MERCEDES BENZ|MERCEDESBENZ': 'MERCEDES',
        'NISSAN\.': 'NISSAN',
        'VOLKSWAGEN VW': 'VOLKSWAGEN',
        'NON DEFINI|NULL': ''
    },
    'modele': {
        'KA\+': 'KA',
        'MEGANERTE\/|MEGANERTE': 'MEGANE',
        #'CLIOCHIPIE|CLIOBEBOP\/|CLIORN\/RT|CLIOBACCAR': 'CLIO I',
        #'CLIOSTE': 'CLIO I',
        'CLIORL\/RN\/|CLIORL\/RN|CLIOS': 'CLIO',
        ' III$': ' 3',
        ' IV$': ' 4',
        'NON DEFINI|NULL': ''
    }
}
marques_dict = {df['marque']: ref_marque_modele[ref_marque_modele['marque'] == df['marque']]['modele'].tolist() for k, df in ref_marque_modele.iterrows()}


def cleaning(row):
    
    marque = (row['marque'] #unidecode(row['CG_MarqueVehicule'])
              .replace('[^\w\s]','')
              .replace('_',' ')
              .upper()
              .strip()
             )

    modele = (row['modele'] #unidecode(row['CG_ModeleVehicule'])
              .strip()
              .upper()
              .replace(marque, '')
              .strip()
             )
    for a, b in replace_regex['marque'].items():
        marque = re.sub(a, b, marque)
    for a, b in replace_regex['modele'].items():
        modele = re.sub(a, b, modele)

    return dict(marque=marque, modele=modele)

tol_marque = 0.85
tol_modele = 0.7

def fuzzymatch(row):

    result = dict(marque='', modele='',score=0)

    match_marque, score_marque, _ = process.extractOne(
                                    row['marque'],
                                    ref_marque_modele['marque']
                                    )

    result['score'] += score_marque

    if match_marque and score_marque > tol_marque:
        result['marque'] = match_marque
        if row['modele'] != '':
            match_modele, score_modele = process.extractOne(
                                            row['modele'], 
                                            marques_dict[match_marque]
                            #scorer=fuzz.partial_token_sort_ratio
                            )

            # print("%s - %s => %d"%(match_modele, row['modele'], score_modele ))

            result['score'] +=  score_modele
            if match_modele and score_modele > tol_modele:
                result['modele'] = match_modele

    result['score'] = result['score']/200.

    return result



def wrap_cleaning(key_row):
    key = key_row[0]
    row = key_row[1]
    new_row =  {'index' : key}
    res = cleaning(row)

    new_row.update(res)
    return  new_row


def wrap_fuzzymatch(key_row):
    key = key_row[0]
    row = key_row[1]
    new_row =  {'index' : key}
    res = fuzzymatch(row)
    new_row.update(res)
    return  new_row

def wrap_cleaning_fuzzymatch(key_row):
    key = key_row[0]
    row = key_row[1]
    new_row =  {'index' : key}
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned)
    new_row.update(cleaned)
    return  new_row

def df_cleaning(df, num_workers):
    # multiprocess le nettoyage
    pool = Pool(num_workers)
    res = pool.map(wrap_cleaning, df.iterrows())
    df_res = pd.DataFrame(res)
    pool.close()

    return  df_res.set_index('index')


def df_fuzzymatch(df, num_workers):
    # fuzzy match pour marque et modele hors des references
    filter = (df['marque'].isin(ref_marque_modele['marque'])) &\
             (df['modele'].isin(ref_marque_modele['modele']))

    df_diff = df[~filter]
    
    if df_diff.empty:
        return df

    # multiprocess le fuzzy
    pool = Pool(num_workers)
    res = pool.map(wrap_fuzzymatch, df_diff.iterrows())
    df_res = pd.DataFrame(res)
    pool.close()
    df.loc[filter,'score'] = 1
    return pd.concat([df_res.set_index('index'), df[filter]],
                        ignore_index=False)


def test_process():
    row = dict(modele='renault clio',marque='renault')
    res = fuzzymatch(cleaning(row))
    assert res == {"marque": "RENAULT", "modele": "CLIO", "score":1}, res
    row = dict(modele='',marque='renault')
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned)
    assert res == {"marque": "RENAULT", "modele": "", "score":0.5}, res


if __name__ == '__main__':
    test_process_df()
