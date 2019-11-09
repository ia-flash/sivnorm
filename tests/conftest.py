# sharing fixture functions
import pytest
import base64
from requests_toolbelt.multipart.encoder import MultipartEncoder

path_table = "tests/test_small.csv"

@pytest.fixture
def apigateway_event():
    """ POST element
    """
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
    print(event)

    yield event
