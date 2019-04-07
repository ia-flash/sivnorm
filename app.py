from flask import Flask, render_template, Response, render_template_string, send_from_directory, request, make_response
import json
import re

from process import cleaning, fuzzymatch, wrap_cleaning
import pandas as pd
from io import StringIO

from multiprocessing import Pool


app = Flask(__name__)


@app.route('/')
def status():
    return json.dumps({'status': 'ok'})

@app.route('/clean')
def clean():
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

@app.route('/clean_csv' ,methods=['POST'])
def clean_csv():

    input_file = request.files['file']
    df = pd.read_csv(input_file, names=['marque','modele'])   
    print(df)

    output_file = StringIO()
    filename = "%s.csv" % ('output file')

    # process
    pool = Pool(32)

    res = pool.map(wrap_cleaning, df.iterrows())
    print(res)
    df_res = pd.DataFrame(res)
    pool.close()

    df_res.sort_index().to_csv(output_file, encoding='utf-8', index=False, header= False)
    output_csv = output_file.getvalue()
    output_file.close()

    resp = make_response(output_csv)
    resp.headers["Content-Disposition"] = ("attachment; filename=%s" % filename)
    resp.headers["Content-Type"] = "text/csv"
    return resp

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
