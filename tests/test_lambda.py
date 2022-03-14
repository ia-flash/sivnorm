import os
import sys
import json
import base64
import pathlib
import pandas as pd
from io import StringIO
from requests_toolbelt.multipart.encoder import MultipartEncoder

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve() / 'aws_lambda'))
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from lambda_function import lambda_handler_norm, lambda_handler_clean


def test_norm_post():
    path_table = "tests/test_small.csv"
    mp_encoder = MultipartEncoder(
            fields={'file': ('filename', open(path_table, "rb"), 'text/csv'),
                    })
    body = mp_encoder.to_string()
    print('form-data is :')
    print(body[:100])
    body = base64.b64encode(body)
    event = dict(httpMethod='POST',
                 path='/norm',
                 pathParameters=dict(table_ref_name='caradisiac'),
                 headers={'content-type': mp_encoder.content_type},
                 body=body)
    resp = lambda_handler_norm(event, None)
    body = resp['body']
    assert resp['statusCode'] == 200
    df_in = pd.read_csv(path_table, header=None)
    df_out = pd.read_csv(StringIO(body), header=None)
    print(df_in)
    print(df_out)
    assert df_in.shape[0] == df_out.shape[0]
    assert (df_in.shape[1] + 1) == df_out.shape[1]
    assert 'renault' in body, 'There is no renault in predictions {}'.format(body)


def test_norm_get():
    event = dict(httpMethod='GET',
                 path='/norm/caradisiac',
                 pathParameters=dict(table_ref_name='caradisiac'),
                 queryStringParameters=dict(
                     marque='renault',
                     modele='clio')
                 )
    resp = lambda_handler_norm(event, None)
    body = resp['body']
    print(body)
    assert resp['statusCode'] == 200
    assert 'modele' in json.loads(resp['body']).keys()
    assert 'renault' in json.loads(resp['body'])['marque'].lower()


def test_clean_get():
    event = dict(httpMethod='GET',
                 path='/clean/caradisiac?marque=renault&modele=clioo',
                 pathParameters=dict(table_ref_name='caradisiac'),
                 queryStringParameters=dict(
                     marque='renault',
                     modele='clio')
                 )
    resp = lambda_handler_clean(event, None)
    body = resp['body']
    print(body)
    assert resp['statusCode'] == 200
    assert 'modele' in json.loads(resp['body']).keys()
    assert 'renault' in json.loads(resp['body'])['marque'].lower()
