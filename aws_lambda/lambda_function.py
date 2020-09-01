import os
import re
import json
import boto3
import pandas as pd
import os.path as osp
from sivnorm.process import cleaning, fuzzymatch, df_process
import base64
from requests_toolbelt.multipart import decoder

pattern = re.compile('(?<=form-data; name=").*?(?=")')

dst_path = os.environ['BASE_MODEL_PATH'] # locally
bucket_name = 'iaflash' # in s3
src_path = 'dss' # in s3 bucket

files = ['esiv_marque_modele_genre.csv', 'caradisiac_marque_modele.csv',
         'esiv_caradisiac_marque_modele_genre.csv']

if not osp.exists(dst_path):
    print("Creating {}".format(dst_path))
    os.makedirs(dst_path)

for file in files:
    dst_path_abs = osp.join(dst_path, file)
    print("Checking for {}".format(dst_path_abs))
    if not osp.isfile(dst_path_abs):
        print("Downloading: {}".format(osp.join(src_path, file)))
        s3 = boto3.resource('s3')
        myobject = s3.Object(bucket_name, osp.join(src_path, file))
        myobject.download_file(dst_path_abs)
        print("Downloading ok\n")
    else:
        print("{} already exist".format(file))

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

    df = df_process(df, table_ref_name, 0)
    print(df)
    return df.sort_index().to_csv(encoding='utf-8', index=False, header=False)


def lambda_handler_norm(event, context):
    queryStringParameters = event.get('queryStringParameters', None)
    pathParameters = event.get('pathParameters', None)
    if pathParameters:
        table_ref_name = pathParameters.get('table_ref_name', '')
    else:
        return {
            'statusCode': 500,
            'body': json.dumps(dict())
        }

    if event["httpMethod"] == "OPTIONS":
        return {
                'headers': {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS"
                    },
                'statusCode': 200,
                }
    elif event["httpMethod"] == "GET":
        marque = queryStringParameters.get('marque', '')
        modele = queryStringParameters.get('modele', '')
        res = json.dumps(process_row(table_ref_name, marque, modele))
        return {
                'headers': {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "GET"
                    },
                'statusCode': 200,
                'body': res
                }

    elif event["httpMethod"] == "POST":
        try:
            event['body'] = base64.b64decode(event['body'])
        except Exception as e:
            print(e)
            return {
                    'statusCode': 400,
                    'body': e
                    }

        if type(event['body']) is str:
            event['body'] = bytes(event['body'], 'utf-8')

        content_type = event.get('headers', {"content-type": ''}).get('content-type')
        multipart_data = decoder.MultipartDecoder(event['body'], content_type)

        for part in multipart_data.parts:
            content_disposition = part.headers.get(b'Content-Disposition', b'').decode('utf-8')
            search_field = pattern.search(content_disposition)
            if search_field:
                if search_field.group(0) == 'file':
                    try:
                        r_csv=part.content.decode('utf-8')
                        lst = [i for i in r_csv.split('\n') if i != '']
                        result = [i.split(',') for i in lst]
                        text_csv = process_csv(table_ref_name, result)
                        return {
                                'headers': {
                                    "Access-Control-Allow-Origin": "*",
                                    "Access-Control-Allow-Headers": "Content-Type",
                                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                                    },
                                'statusCode': 200,
                                'body': text_csv,
                                #"content-type": "text/csv",
                                #"content-disposition": "attachment; \
                                #        filename=output file.csv"
                                }
                    except Exception as e:
                        return {
                                'statusCode': 400,
                                'body': e
                                }
                else:
                    return {
                            'statusCode': 402,
                            'body': 'Bad field name in form-data'
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
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
            'statusCode': 200,
            'body': json.dumps(res)
            }
