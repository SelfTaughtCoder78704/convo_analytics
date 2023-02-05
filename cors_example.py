from flask_cors import CORS

approved_sites = ['client1.com', 'client2.com']


def allow_cors(response):
    origin = request.headers.get('Origin', '')
    if origin in approved_sites:
        response.headers['Access-Control-Allow-Origin'] = origin
    return response


app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}},
            attach_to_all=False, automatic_options=False)
app.after_request(allow_cors)
