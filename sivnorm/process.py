import json
import re
from fuzzywuzzy import process, fuzz
from unidecode import unidecode
import pandas as pd

from multiprocessing import Pool
from functools import partial

# dict_siv = pd.read_csv('/dss/esiv_by_cnit_python.csv').set_index('cnit_tvv').to_dict('index')


ref_marque_modele = dict(siv=pd.read_csv('/dss/esiv_marque_modele_genre.csv'),
                        caradisiac=pd.read_csv('/dss/caradisiac_marque_modele.csv').rename(columns={'alt':'modele'}),
                        siv_caradisiac=pd.read_csv('/dss/esiv_caradisiac_marque_modele_genre.csv'))

def hash_table1(x):
    assert 'marque' in ref_marque_modele[x].columns
    assert 'modele' in ref_marque_modele[x].columns

    return  {df['marque']: ref_marque_modele[x].loc[ref_marque_modele[x]['marque'] == df['marque'],'modele'].tolist() for k, df in ref_marque_modele[x].iterrows()}

def hash_table2(x):
    assert 'marque' in ref_marque_modele[x].columns
    assert 'modele' in ref_marque_modele[x].columns
    assert 'href' in ref_marque_modele[x].columns # link ref
    assert 'src' in ref_marque_modele[x].columns # image ref source
    gp = ref_marque_modele[x].groupby(['marque','modele'])
    if  not (gp.size() == 1).all():
        print("Be careful, your mapping %s is not unique"%x)
        print("take first of :")
        print(gp.size()[gp.size()>1])
    # assert (gp == 1).all(),

    return  gp.first().to_dict('index')

# dictionnaire pour acceder rapidement à tous les modeles d'une marque
marques_dict = {x:hash_table1(x) for x in ['siv','caradisiac','siv_caradisiac']}

# dictionnaire pour acceder rapidement à href et src (images de caradisiac)
src_dict = {x:hash_table2(x) for x in ['siv','caradisiac','siv_caradisiac']}

reg_class = lambda x : '^(CLASSE ?)?{x} *[0-9]+(.*)'.format(x=x)
reg_no_class = lambda x : '^(CLASSE ?){x}'.format(x=x)

replace_regex = {
    'marque': {
        'BW|B\.M\.W\.|B\.M\.W|BMW I': 'BMW',
        'FIAT\.': 'FIAT',
        'MERCEDES BENZ|MERCEDESBENZ|MERCEDES-BENZ': 'MERCEDES',
        'NISSAN\.': 'NISSAN',
        'VOLKSWAGEN VW': 'VOLKSWAGEN',
        'NON DEFINI|NULL': ''
    },
    'modele': {
        'KA\+': 'KA',
        'MEGANERTE\/|MEGANERTE': 'MEGANE',
        'MEGANE SCENIC' : 'SCENIC',
        'MEGANESCENIC' : 'SCENIC',
        '(.*)ARA PIC(.*)' :  'XSARA PICASSO', # XARA PICA -> XSARA PICASSO
        '(.*)ARAPIC(.*)' :  'XSARA PICASSO',
        #'CLIOCHIPIE|CLIOBEBOP\/|CLIORN\/RT|CLIOBACCAR': 'CLIO I',
        #'CLIOSTE': 'CLIO I',
        'CLIORL\/RN\/|CLIORL\/RN|CLIOS' : 'CLIO',
        ' III$': ' 3',
        ' IV$': ' 4',
        'NON DEFINI|NULL' : '',
        'BLUETEC|TDI|CDI' : '',
        'REIHE' : 'SERIE'

    },

    'MERCEDES': {**{reg_class(x) : 'CLASSE %s'%x for x in ['A','B','C','E','G','S','V','X']},
                 **{reg_no_class(x) : '%s'%x for x in ['CL','GL','SL']}},

    'RENAULT' : {' ?(SOCIETE)' : ''}
    }


def cleaning(row):

    marque = (str(row['marque']) #unidecode(row['CG_MarqueVehicule'])
              .replace('[^\w\s]','')
              .replace('_',' ')
              .upper()
              .strip()
             )

    modele = (str(row['modele']) #unidecode(row['CG_ModeleVehicule'])
              .strip()
              .upper()
              .replace(marque, '')
              .strip()
             )

    for a, b in replace_regex['marque'].items():
        marque = re.sub(a, b, marque)
    for a, b in replace_regex['modele'].items():
        modele = re.sub(a, b, modele)

    # Renplacement conditionnel du modele
    if marque in replace_regex.keys():
        for  a, b in replace_regex[marque].items():
            modele = re.sub(a, b, modele)

    return dict(marque=marque, modele=modele)

tol_marque = 0.85
tol_modele = 0.7

def fuzzymatch(row, table_ref_name='siv'):

    result = dict(marque='', modele='',score=0)

    try:
        match_marque, score_marque, _ = process.extractOne(
                                        str(row['marque']),
                                        ref_marque_modele[table_ref_name]['marque']
                                        )
    except Exception as e:
        print(e)
        score_marque = 0
        match_marque = None
        print(row['marque'])
        print('Cannot be matched with :')
        print(ref_marque_modele[table_ref_name]['marque'])

    result['score'] += score_marque

    if match_marque and score_marque > tol_marque:
        result['marque'] = match_marque
        if row['modele'] != '':
            try:
                match_modele, score_modele = process.extractOne(
                                                str(row['modele']),
                                                marques_dict[table_ref_name][match_marque],
                                                scorer=fuzz.ratio
                                )

            except Exception as e:
                print(e)
                score_modele = 0
                match_modele = None
                print(row['modele'])
                print('Cannot be matched with :')
                print(marques_dict[table_ref_name][match_marque])

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


def wrap_fuzzymatch(table_ref_name, key_row):
    key = key_row[0]
    row = key_row[1]
    new_row =  {'index' : key}
    res = fuzzymatch(row, table_ref_name)
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


def df_fuzzymatch(df, table_ref_name, num_workers):
    # fuzzy match pour marque et modele hors des references
    filter = (df['marque'].isin(ref_marque_modele[table_ref_name]['marque'])) &\
             (df['modele'].isin(ref_marque_modele[table_ref_name]['modele']))

    df_diff = df[~filter]
    # multiprocess le fuzzy
    pool = Pool(num_workers)
    func = partial(wrap_fuzzymatch, table_ref_name)
    res = pool.map(func, df_diff.iterrows())
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
