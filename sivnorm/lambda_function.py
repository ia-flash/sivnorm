import json
from process import cleaning, fuzzymatch


def process_row(table_ref_name, marque, modele):
    if marque and modele:
        row = dict(modele=modele, marque=marque)
        for column in ['marque', 'modele']:
            row = fuzzymatch(cleaning(row, column), column, table_ref_name)
        row['score'] = (row['score_marque'] + row['score_modele']) / 200
        return row


def lambda_handler_norm(event, context):
    queryStringParameters = event.get('queryStringParameters', None)
    pathParameters = event.get('pathParameters', None)
    if queryStringParameters and pathParameters:
        marque = queryStringParameters.get('marque', '')
        modele = queryStringParameters.get('modele', '')
        table_ref_name = pathParameters.get('table_ref_name', '')
        res = process_row(table_ref_name, marque, modele)
    else:
        res = dict()
    return {
        'statusCode': 200,
        'body': json.dumps(res)
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

