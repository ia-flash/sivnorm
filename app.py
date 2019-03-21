from flask import Flask, render_template, Response, render_template_string, send_from_directory, request
import json
import re
from fuzzywuzzy import process, fuzz
from unidecode import unidecode
import pandas as pd

app = Flask(__name__)

global dict_siv
global df_marque_modele

dict_siv = pd.read_csv('/dss/esiv_by_cnit_python.csv').set_index('cnit_tvv').to_dict('index')
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

def fuzzymatch(string):
    marque, modele = string.split("_")
    match_marque = process.extractOne(
            marque,
            df_marque_modele['marque']
            ) #, scorer=fuzz.partial_token_sort_ratio)

    if match_marque[1] > 85 and modele:
        match_modele = process.extractOne(modele, marques_dict[match_marque[0]], scorer=fuzz.partial_token_sort_ratio)
        if match_modele and match_modele[1] > 70:
            marque_modele = "{}_{}".format(match_marque[0], match_modele[0])
            return df_marque_modele[(df_marque_modele['marque'] == match_marque[0]) & (df_marque_modele['modele'] == match_modele[0])][['marque', 'modele', 'cnit_tvv_distinct']].to_dict(orient='records')[0]
        else:
            return None
    else:
        return None


def cleaning(row):
    marque = (row['CG_MarqueVehicule'] #unidecode(row['CG_MarqueVehicule'])
              .replace('[^\w\s]','')
              .replace('_',' ')
              .upper()
              .strip()
             )
    modele = (row['CG_ModeleVehicule'] #unidecode(row['CG_ModeleVehicule'])
              .strip()
              .upper()
              .replace(marque, '')
              .strip()
             )
    for a, b in replace_regex['marque'].items():
        marque = re.sub(a, b, marque)
    for a, b in replace_regex['modele'].items():
        modele = re.sub(a, b, modele)

    new_row = dict(row)
    if marque != '':
        result = fuzzymatch("{}_{}".format(marque, modele))
        new_row.update({"CG_marque_modele": "{}_{}".format(marque, modele)})
        if result:
            result = {k: unidecode(v) if type(v) == str else v for k,v in 
                    result.items()}
            new_row.update(result)
    return new_row

@app.route('/')
def status():
    return json.dumps({'status': 'ok'})

@app.route('/clean')
def clean():
    marque = request.args.get('marque',None)
    modele = request.args.get('modele',None)
    cnit = request.args.get('cnit',None)

    if cnit:
        print('CNIT : %s'%cnit)
        info = dict_siv.get(cnit,None)
        print(info)
        if info:
            marque = info.get('marque',None)
            modele = info.get('modele',None)
            return json.dumps(dict(marque=marque,modele=modele))

    if marque and modele:
        result = cleaning({"CG_MarqueVehicule": marque, "CG_ModeleVehicule": 
            modele})

    if 'cnit_tvv_distinct' in result:
        return json.dumps(dict(marque=result['marque'],modele=result['modele'], cnit=result['cnit_tvv_distinct']))
    else:
        return json.dumps(dict(marque=marque,modele=modele,status='not found'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
