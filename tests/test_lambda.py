import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__),'../aws_lambda'))
from lambda_function import lambda_handler_norm, lambda_handler_clean


def test_norm_post(apigateway_event):
    resp = lambda_handler_norm(apigateway_event, None)
    body = resp['body']
    print('thisbody')
    print(body)
    assert resp['statusCode'] == 200
    assert 'renault' in body, 'There is no clio in predictions {}'.format(body)


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
