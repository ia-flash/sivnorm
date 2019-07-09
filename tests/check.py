import sys
import pandas as pd
import requests
from io import StringIO
from fuzzywuzzy import process, fuzz

sys.path.append('./sivnorm')
from process import marques_dict


def test_check():
    df_in = pd.read_csv(
            './tests/test_small.csv', names=['marque', 'modele'],
            usecols=[0, 1], encoding='utf-8')
    df_ref = pd.read_csv(
            './tests/test_small.csv', names=['marque', 'modele'],
            usecols=[2, 3], encoding='utf-8')
    df_in = df_in.fillna("")
    df_ref = df_ref.fillna("")

    f = StringIO()
    df_in.to_csv(f, encoding='utf-8', index=False, header=False)
    files = {'file': ('file.csv', f.getvalue())}
    f.close()

    url = 'http://localhost:5000/sivnorm/norm/caradisiac'
    r = requests.post(url, files=files)
    df_pred = pd.read_csv(StringIO(r.text), names=['marque', 'modele', 'score'], encoding='utf-8')
    print(pd.concat([df_in, df_pred], axis=1))
    df_pred = df_pred.fillna("")

    report = '!!  %s --> %s rather than %s for row %s  !!'
    for (row, inp), (_, ref), (_, pred) in zip(df_in.iterrows(), df_ref.iterrows(), df_pred.iterrows()):
        #print(type(ref.modele), type(pred.modele))
        #print(ref.marque, pred.marque)
        print(50*"*")

        if ref.modele != pred.modele:
            print(report % (inp.modele, pred.modele, ref.modele, row+1))
        if ref.marque != pred.marque:
            print(report % (inp.marque, pred.marque, ref.marque, row+1))

        print(inp.modele, ref.modele)

        if ref.marque in marques_dict['caradisiac'].keys():
            choices = marques_dict['caradisiac'][ref.marque]
            candidates = process.extract(inp.modele, choices, limit=5, scorer=fuzz.WRatio)
            print(candidates)


if __name__ == '__main__':
    test_check()
