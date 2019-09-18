import re
import os
import os.path as osp
from fuzzywuzzy import process, fuzz
from unidecode import unidecode
import pandas as pd
import boto3
from multiprocessing import Pool
from functools import partial

dst_path = os.environ['BASE_MODEL_PATH'] # locally
bucket_name = 'iaflash' # in s3
src_path = 'dss' # in s3 bucket

files = ['esiv_marque_modele_genre.csv', 'caradisiac_marque_modele.csv',
         'esiv_caradisiac_marque_modele_genre.csv']

if not osp.exists(dst_path):
    print("Creating {}".format(dst_path))
    os.makedirs(dst_path)

for file in files:
    if not osp.isfile(osp.join(dst_path, file)):
        print("Downloading: {}".format(osp.join(src_path, file)))
        s3 = boto3.resource('s3')
        myobject = s3.Object(bucket_name, osp.join(src_path, file))
        myobject.download_file(osp.join(dst_path, file))
        print("Downloading ok\n")
    else:
        print("{} already exist".format(file))

ref_marque_modele_path = dict(
        siv=osp.join(dst_path, 'esiv_marque_modele_genre.csv'),
        caradisiac=osp.join(dst_path, 'caradisiac_marque_modele.csv'),
        siv_caradisiac=osp.join(dst_path, 'esiv_caradisiac_marque_modele_genre.csv')
        )

ref_marque_modele = dict()
for key, value in ref_marque_modele_path.items():
    if os.path.exists(value):
        ref_marque_modele[key] = pd.read_csv(value).rename(columns={'alt': 'modele'})

def hash_table1(x):
    assert 'marque' in ref_marque_modele[x].columns
    assert 'modele' in ref_marque_modele[x].columns

    return ref_marque_modele[x].groupby(['marque']).apply(lambda x: x['modele'].to_list()).to_dict()


def hash_table2(x):
    assert 'marque' in ref_marque_modele[x].columns
    assert 'modele' in ref_marque_modele[x].columns
    assert 'href' in ref_marque_modele[x].columns  # link ref
    assert 'src' in ref_marque_modele[x].columns  # image ref source
    gp = ref_marque_modele[x].groupby(['marque', 'modele'])
    if not (gp.size() == 1).all():
        print("Be careful, your mapping %s is not unique"%x)
        print("take first of :")
        print(gp.size()[gp.size()>1])
    # assert (gp == 1).all(),

    return gp.first().to_dict('index')

# dictionnaire pour acceder rapidement à tous les modeles d'une marque
marques_dict = {x: hash_table1(x) for x in ref_marque_modele.keys()}

# dictionnaire pour acceder rapidement à href et src (images de caradisiac)
src_dict = {x: hash_table2(x) for x in ref_marque_modele.keys()}


def reg_class(x):
    return '^(CLASSE ?)?{x} *[0-9]+(.*)'.format(x=x)


def reg_no_class(x):
    # '^(CLASSE ?){x}(?:\w)(.*)'
    return '^(CLASSE ?){x}'.format(x=x)


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
        'MEGANE SCENIC': 'SCENIC',
        'MEGANESCENIC': 'SCENIC',
        '(.*)ARA PIC(.*)':  'XSARA PICASSO', # XARA PICA -> XSARA PICASSO
        '(.*)ARAPIC(.*)':  'XSARA PICASSO',
        #'CLIOCHIPIE|CLIOBEBOP\/|CLIORN\/RT|CLIOBACCAR': 'CLIO I',
        #'CLIOSTE': 'CLIO I',
        'CLIORL\/RN\/|CLIORL\/RN|CLIOS' : 'CLIO',
        ' III$': ' 3',
        ' IV$': ' 4',
        'NON DEFINI|NULL': '',
        'BLUETEC|TDI|CDI': '',
        'BLUETEC|TDI|CDI': '',
        'REIHE': 'SERIE'
    },
    'MERCEDES': {**{reg_class(x): 'CLASSE %s'%x for x in ['A','B','C','E','G','S','V','X']},
                 **{reg_no_class(x): '%s'%x for x in ['CL', 'GL', 'SL']}},
    'RENAULT': {' ?(SOCIETE)': ''},
    'BMW': {'(SERIE ?){x}'.format(x=x): '{x}'.format(x=x) for x in ['I', 'M', 'Z', 'X']}
    }


def cleaning(row: dict, column: str):
    """Cleaning function

    Args:
        row: Detected boxes
        column: Image used for detection

    Returns:
        row: Cleaned marque and model
    """
    if column == 'marque':
        row['marque'] = (
                unidecode(row['marque'])
                .replace('[^\w\s]', '')
                .replace('_', ' ')
                .replace('-', '')
                .upper()
                .strip()
                 )

    elif column == 'modele':
        row['modele'] = (
                unidecode(row['modele'])
                .strip()
                .upper()
                .strip()
                 )

    if row['marque'] not in ['MINI', 'DS']:
        row['modele'] = row['modele'].replace(row['marque'], '').strip()

    for a, b in replace_regex[column].items():
        row[column] = re.sub(a, b, row[column])

    # Renplacement conditionnel du modele
    if column == 'modele':
        if row['marque'] in replace_regex.keys():
            for a, b in replace_regex[row['marque']].items():
                row['modele'] = re.sub(a, b, row['modele'])

    return row


tol = dict(marque=0.85, modele=0.7)


def fuzzymatch(row, column='marque', table_ref_name='siv'):
    score = 0
    match = ''

    if row[column] == '' or (column == 'modele' and row['score_marque'] < tol['marque']):
        row[column] = match
        row['score_%s'%column] = score
        return row

    try:
        if column == 'marque':
            choices = ref_marque_modele[table_ref_name][column].to_list()
            match, score = process.extractOne(
                                            str(row[column]),
                                            choices,
                                            )
        elif column == 'modele':
            choices = marques_dict[table_ref_name][row['marque']]
            match, score = process.extractOne(
                                            str(row[column]),
                                            choices,
                                            scorer=fuzz.WRatio
                            )

    except Exception as e:
        print(e)
        print(row[column])
        print('Cannot be matched with :')

    # print("%s => %s (%d)"%(row[column], match, score))

    if score > tol[column]:
        row[column] = match

    row['score_%s'%column] = score

    return row


def wrap_cleaning(column, key_row):
    key = key_row[0]
    row = key_row[1]
    new_row = {'index': key}
    res = cleaning(row, column)

    new_row.update(res)
    return new_row


def wrap_fuzzymatch(table_ref_name, column, key_row):
    key = key_row[0]
    row = key_row[1]
    new_row = {'index': key}
    res = fuzzymatch(row, column, table_ref_name)
    new_row.update(res)
    return new_row


def df_cleaning(df, column, num_workers):
    # multiprocess le nettoyage
    pool = Pool(num_workers)
    func = partial(wrap_cleaning, column)
    res = pool.map(func, df.iterrows())
    df_res = pd.DataFrame(res)
    pool.close()

    return df_res.set_index('index').sort_index()


def df_fuzzymatch(df, column, table_ref_name, num_workers):
    # fuzzy match pour marque et modele hors des references
    if column == 'marque':
        filter = df[column].isin(ref_marque_modele[table_ref_name][column].to_list())
    elif column == 'modele':
        filter = df.eval('marque + modele').isin(ref_marque_modele[table_ref_name].eval('marque + modele'))

    df.loc[filter,'score_%s'%column] = 100
    df.loc[~filter,'score_%s'%column] = 0

    # multiprocess le fuzzy
    pool = Pool(num_workers)
    func = partial(wrap_fuzzymatch, table_ref_name, column)
    res = pool.map(func, df[~filter].iterrows())
    df_res = pd.DataFrame(res)
    pool.close()

    return pd.concat([df_res, df[filter].reset_index()]).set_index('index').sort_index()

dict_post_cleaning = {'caradisiac':
                                {
                                ('CITROEN', 'DS3') : ('DS', 'DS 3')
                                }
                    }

def df_post_cleaning(df, table_ref_name):

    for before, after in dict_post_cleaning.get(table_ref_name, {}).items():
    # mitght wnat to instal numexp for optim
        filter = df.eval('marque == "%s" and modele == "%s"'%before)
        df.loc[filter,'marque'] = after[0]
        df.loc[filter,'modele'] = after[1]

    return df


def df_process(df, table_ref_name, num_workers):
    for column in ['marque', 'modele']:
        df = df_cleaning(df, column, num_workers)
        df = df_fuzzymatch(df, column, table_ref_name, num_workers)

    df = df_post_cleaning(df, table_ref_name)

    df['score'] = (df['score_marque'] + df['score_modele']) / 200

    return df[['marque', 'modele', 'score']]


def test_process():
    row = dict(modele='renault clio', marque='renault')
    res = fuzzymatch(cleaning(row))
    assert res == {"marque": "RENAULT", "modele": "CLIO", "score": 1}, res
    row = dict(modele='', marque='renault')
    cleaned = cleaning(row)
    res = fuzzymatch(cleaned)
    assert res == {"marque": "RENAULT", "modele": "", "score": 0.5}, res


if __name__ == '__main__':
    test_process()
