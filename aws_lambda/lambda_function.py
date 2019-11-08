import re
import json
import pandas as pd
from sivnorm.process import cleaning, fuzzymatch, df_process
import base64


def process_row(table_ref_name, marque, modele):
    if marque and modele:
        row = dict(modele=modele, marque=marque)
        for column in ['marque', 'modele']:
            row = fuzzymatch(cleaning(row, column), column, table_ref_name)
        row['score'] = (row['score_marque'] + row['score_modele']) / 200
        return row


def process_csv(table_ref_name, input_file):
    df = pd.DataFrame(input_file, columns=['marque', 'modele'])

    df = df.fillna("")

    df = df_process(df, table_ref_name, 1)
    print(df)
    return df.sort_index().to_csv(encoding='utf-8', index=False, header=False)


def lambda_handler_norm(event, context):
    #print("HERE")
    #print(event)
    queryStringParameters = event.get('queryStringParameters', None)
    pathParameters = event.get('pathParameters', None)
    if queryStringParameters and pathParameters:
        marque = queryStringParameters.get('marque', '')
        modele = queryStringParameters.get('modele', '')
        table_ref_name = pathParameters.get('table_ref_name', '')
        res = json.dumps(process_row(table_ref_name, marque, modele))
    elif event["httpMethod"] == "POST":
        table_ref_name = pathParameters.get('table_ref_name', '')

        decoded_string = base64.b64decode(event['body'])
        print(decoded_string.decode("utf-8"))

        r_csv = re.search(r'Content-Type: application/octet-stream\r\n\r(.*\,\w)',
                          decoded_string.decode("utf-8"), re.DOTALL)
        lst = [i for i in r_csv.group(1).split('\n') if i != '']
        result = [i.split(',') for i in lst]
        print(result)
        # #mp.pool not implemented in lambda
        # res = process_csv(table_ref_name, result)
        res = result
    else:
        res = json.dumps(dict())
    return {
        'statusCode': 200,
        'body': res
    }


def lambda_handler_clean(event, context):
    queryStringParameters = event.get('queryStringParameters', None)
    if queryStringParameters:
        marque = queryStringParameters.get('marque', '')
        modele = queryStringParameters.get('modele', '')
        row = dict(marque=marque, modele=modele)
        for column in ['marque', 'modele']:
            res = cleaning(row, column)
    else:
        res = dict()
    return {
        'statusCode': 200,
        'body': json.dumps(res)
    }
