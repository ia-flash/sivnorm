from flask import Flask, render_template, Response, render_template_string, send_from_directory, request, make_response
import json
import re
import time
from process import  cleaning, fuzzymatch, df_cleaning, df_fuzzymatch,  ref_marque_modele

import pandas as pd
from io import StringIO

from multiprocessing import Pool


app = Flask(__name__)


@app.route('/')
def status():
    return json.dumps({'status': 'ok'})

def process_row():
    marque = request.args.get('marque',None)
    modele = request.args.get('modele',None)
    cnit = request.args.get('cnit',None)


    print('CNIT : %s'%cnit)
    print('MARQUE : %s'%marque)
    print('MODELE : %s'%modele)

    if marque and modele:
        cleaned = cleaning(request.args)
        matched = fuzzymatch(cleaned)
        return json.dumps(matched)

    if cnit:
        info = dict_siv.get(cnit,None)
        print(info)
        if info:
            marque = info.get('marque',None)
            modele = info.get('modele',None)
            return json.dumps(dict(marque=marque,modele=modele))

 
def process_csv():

    workers = 10
    filename = "%s.csv" % ('output file')

    input_file = request.files['file']
    output_file = StringIO()


    df = pd.read_csv(input_file, names=['marque','modele'])
    print(10*"*")
    print(df)

    t1 = time.time()
    df = df_cleaning(df, workers)
    df_res = df_fuzzymatch(df, workers)
    sec_wl = (workers*(time.time() - t1))/(df.shape[0])
    print( "%.2f seconds per worker per line" % sec_wl )


    df_res.sort_index().to_csv(output_file, encoding='utf-8', index=False, header= False)
    output_csv = output_file.getvalue()
    output_file.close()

    resp = make_response(output_csv)
    resp.headers["Content-Disposition"] = ("attachment; filename=%s" % filename)
    resp.headers["Content-Type"] = "text/csv"

    return resp

@app.route('/norm' ,methods=['GET','POST'])
def norm():
    if request.method == 'GET':
        return process_row()
    elif request.method == 'POST':
        return process_csv()

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
