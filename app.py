from flask import Flask, render_template, Response, render_template_string, send_from_directory, request
import json
import pandas as pd

app = Flask(__name__)

global dict_siv
global df_marque_modele

dict_siv = pd.read_csv('/dss/esiv_by_cnit_python.csv').set_index('cnit_tvv').to_dict('index')
df_marque_modele = pd.read_csv('/dss/esiv_marque_modele_genre.csv')

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



    # find closest thanks to fuzzy matching by Cristian

    return json.dumps(dict(marque=marque,modele=modele))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
