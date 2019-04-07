import json
import re
from fuzzywuzzy import process, fuzz
from unidecode import unidecode
import pandas as pd

from multiprocessing import Pool


# dict_siv = pd.read_csv('/dss/esiv_by_cnit_python.csv').set_index('cnit_tvv').to_dict('index')
df_marque_modele = pd.read_csv('/dss/esiv_marque_modele_genre.csv')


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
marques_dict = {df['marque']: df_marque_modele[df_marque_modele['marque'] == df['marque']]['modele'].tolist() for k, df in df_marque_modele.iterrows()}


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

    """

    new_row = dict(row)
    if marque != '':
        marque, modele = fuzzymatch(marque, modele)
        new_row.update({"CG_marque_modele": "{}_{}".format(marque, modele)})
        if result:
            result = {k: unidecode(v) if type(v) == str else v for k,v in 
                    result.items()}
            new_row.update(result)
    """
    return dict(marque=marque, modele=modele)

def fuzzymatch(row):

    match_marque = process.extractOne(
            row['marque'],
            df_marque_modele['marque']
            ) 

    result = dict(marque='', modele='')
    if match_marque and match_marque[1] > 85:
        result['marque'] = match_marque[0] 
        if row['modele'] != '':
            match_modele = process.extractOne(row['modele'], marques_dict[match_marque[0]], scorer=fuzz.partial_token_sort_ratio)
            if match_modele and match_modele[1] > 70:
                result['modele'] = match_modele[0]


    return result


def test_process():
    row = dict(modele='renault clio',marque='renault')
    assert fuzzymatch(cleaning(row)) == {"marque": "RENAULT", "modele": "CLIO"}
    row = dict(modele='',marque='renault')
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned) 
    assert res == {"marque": "RENAULT", "modele": ""}, res


func = lambda row : cleaning(fuzzymatch(row))

def wrap_cleaning(key_row):
    key = key_row[0]
    row = key_row[1]
    new_row =  {'index' : key}
    cleaned = cleaning(row)
    #res = fuzzymatch(cleaned) 

    new_row.update(cleaned)
    return  res


def test_process_df():
    data = [['renault','clio'],
            ['renault','clio2'],
            ['renault','renault clio7']]

    #data = int(1e6)*[['renault','clio']]

    df = pd.DataFrame(columns=['marque','modele'],data=data)

    pool = Pool(10)

    res = pool.map(wrap_cleaning, df.iterrows())
    print(res)
    df_res = pd.DataFrame(res)
   
    print(df_res)
    pool.close()

if __name__ == '__main__':
    test_process_df()