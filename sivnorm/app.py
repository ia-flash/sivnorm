import os
import time
import pandas as pd
from io import StringIO
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import Flask, request, send_from_directory, make_response, Blueprint, url_for
from flask_restplus import Resource, Api, reqparse, fields
from flask_cors import CORS
from process import cleaning, fuzzymatch, src_dict, df_process
from werkzeug.datastructures import FileStorage
from utils import timeit, logger

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
CORS(app)

if os.getenv('APP_PORT'):
    PORT = int(str(os.getenv('APP_PORT')))
else:
    PORT=5000

##########################
#  Documentation Sphinx  #
##########################

blueprint_doc = Blueprint('documentation', __name__,
                          static_folder='../docs/build/html/_static',
                          url_prefix='/sivnorm/docs')


@blueprint_doc.route('/', defaults={'filename': 'index.html'})
@blueprint_doc.route('/<path:filename>')
def show_pages(filename):
    return send_from_directory('../docs/build/html', filename)


app.register_blueprint(blueprint_doc)


#################
#  API SWAGGER  #
#################


class Custom_API(Api):
    @property
    def specs_url(self):
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :rtype: str
        '''
        return url_for(self.endpoint('specs'), _external=False)


blueprint = Blueprint('api', __name__, url_prefix='/sivnorm')
api = Custom_API(
        blueprint, doc='/swagger', version='1.0', title='SivNorm',
        description="Match flou de la marque et modèle des véhicules dans la \
                carte grise à partir d'un référentiel")
app.register_blueprint(blueprint)


@timeit
def process_row(table_ref_name, marque, modele):
    if marque and modele:
        row = dict(modele=modele, marque=marque)
        for column in ['marque', 'modele']:
            row = fuzzymatch(cleaning(row, column), column, table_ref_name)
        row['score'] = (row['score_marque'] + row['score_modele']) / 200
        return row


@timeit
def process_csv(table_ref_name, input_file):

    num_workers = 16
    filename = "%s.csv" % ('output file')

    output_file = StringIO()

    df = pd.read_csv(input_file, names=['marque', 'modele'])

    df = df.fillna("")

    t1 = time.time()
    df = df_process(df, table_ref_name, num_workers)

    sec_wl = (num_workers*(time.time() - t1))/(df.shape[0])
    logger.debug(f'{sec_wl:.2f} seconds per worker per line')

    df.sort_index().to_csv(output_file, encoding='utf-8', index=False, header=False)
    output_csv = output_file.getvalue()
    output_file.close()

    resp = make_response(output_csv)
    resp.headers["Content-Disposition"] = ("attachment; filename=%s" % filename)
    resp.headers["Content-Type"] = "text/csv"

    return resp


parser = reqparse.RequestParser()
parser.add_argument('marque', type=str, location='args', help='Vehicle brand (eg: Renault)')
parser.add_argument('modele', type=str, location='args', help='Vehicle model (eg: Clio)')

parser_table = reqparse.RequestParser()
parser_table.add_argument('file', type=FileStorage, location='files', help='CSV file with multiple brand model lines with no header. Like: \n\n renault,clio \n renault,clio2 \n audi,TTs \n renault,renault clio7 \n renault,clio7 RT/RN')

NormOutput = api.model('NormalizedOutput', {
    'modele': fields.String(description='Matched model', example='Clio'),
    'marque': fields.String(description='Matched brand', example='Renault'),
    'score_marque': fields.Integer(description='Matching score for brand', min=0, max=100, example=100),
    'score_modele': fields.Integer(description='Matching score for model', min=0, max=100, example=100),
    'score': fields.Float(description='Global matching score. Combination of score_marque and score_modele', min=0, max=1, example=1),
})


CleanOutput = api.model('CleanOutput', {
    'modele': fields.String(description='Cleaned model', example='CLIO'),
    'marque': fields.String(description='Cleaned brand', example='RENAULT'),
})


@api.route('/norm/<string:table_ref_name>')
@api.doc(params={'table_ref_name': 'Reference table [siv,cardisiac,siv_caradisiac]'})
class Normalization(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    @api.marshal_with(NormOutput, mask=None)
    def get(self, table_ref_name):
        """Normalize a single brand and model using a defined referential table"""
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')

        logger.debug(f'MARQUE: {marque}')
        logger.debug(f'MODELE: {modele}')
        return process_row(table_ref_name, marque, modele)

    @api.expect(parser_table)
    @api.response(200, description='CSV file containing matching brand model and score like: \n\n RENAULT,CLIO,1.0\n RENAULT,CLIO,0.945 \n AUDI, TTS,1.0 \n RENAULT,CLIO,0.945 \n RENAULT,CLIO,0.95 \n RENAULT,CLIO,1.0')
    @api.produces(['text/csv'])
    def post(self, table_ref_name):
        """Normalize a table of brand and model using a defined referential table"""
        input_file = request.files['file']
        return process_csv(table_ref_name, input_file)


@api.route('/info/<string:table_ref_name>', doc=False)
@api.doc(params={'table_ref_name': 'Reference table [siv,cardisiac,siv_caradisiac]'})
class Information(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    def get(self, table_ref_name):
        """Get brand and model image"""
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')

        res_def = {'src': None, 'href': None}
        res = src_dict.get(table_ref_name, {}).get((marque, modele), res_def)
        return res


@api.route('/clean')
class Clean(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    @api.marshal_with(CleanOutput, mask=None)
    def get(self):
        """Clean brand and model field"""
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')
        row = dict(marque=marque, modele=modele)
        for column in ['marque', 'modele']:
            res = cleaning(row, column)
        return res


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
