import time
import pandas as pd
from io import StringIO
from flask import Flask, request, send_from_directory, make_response, Blueprint, url_for
from flask_restplus import Resource, Api, reqparse
from flask_cors import CORS
from process import cleaning, fuzzymatch, src_dict, df_process

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
CORS(app)

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


def process_row(table_ref_name, marque, modele):
    if marque and modele:
        row = dict(modele=modele, marque=marque)
        for column in ['marque', 'modele']:
            row = fuzzymatch(cleaning(row, column), column, table_ref_name)
        row['score'] = (row['score_marque'] + row['score_modele']) / 200
        return row


def process_csv(table_ref_name):

    num_workers = 16
    filename = "%s.csv" % ('output file')

    input_file = request.files['file']
    output_file = StringIO()

    df = pd.read_csv(input_file, names=['marque', 'modele'])

    df = df.fillna("")

    #print(10*"*"+" Input "+10*"*")
    #print(df)

    t1 = time.time()
    df = df_process(df, table_ref_name, num_workers)

    sec_wl = (num_workers*(time.time() - t1))/(df.shape[0])
    print("%.2f seconds per worker per line" % sec_wl)

    df.sort_index().to_csv(output_file, encoding='utf-8', index=False, header=False)
    output_csv = output_file.getvalue()
    output_file.close()

    resp = make_response(output_csv)
    resp.headers["Content-Disposition"] = ("attachment; filename=%s" % filename)
    resp.headers["Content-Type"] = "text/csv"

    return resp


parser = reqparse.RequestParser()
parser.add_argument('marque', type=str, location='args', help='Marque')
parser.add_argument('modele', type=str, location='args', help='Modele')


@api.route('/norm/<string:table_ref_name>')
@api.doc(params={'table_ref_name': 'Reference table'})
class Normalization(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    def get(self, table_ref_name):
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')

        print('MARQUE : %s'%marque)
        print('MODELE : %s'%modele)
        return process_row(table_ref_name, marque, modele)

    def post(self, table_ref_name):
        return process_csv(table_ref_name)


@api.route('/info/<string:table_ref_name>')
@api.doc(params={'table_ref_name': 'Reference table'})
class Information(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    def get(self, table_ref_name):
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')

        res_def = {'src': None, 'href': None}
        res = src_dict.get(table_ref_name, {}).get((marque, modele), res_def)
        return res


@api.route('/clean')
class Clean(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    def get(self):
        marque = request.args.get('marque', '')
        modele = request.args.get('modele', '')
        row = dict(marque=marque, modele=modele)
        for column in ['marque', 'modele']:
            res = cleaning(row, column)
        return res


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
