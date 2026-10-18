import os
from flask import Flask, jsonify, render_template
from .db import init_db
from .routes import api
from .metrics import Metrics

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(DATABASE=os.getenv('TRIAGEPULSE_DB', os.path.join(app.instance_path, 'triagepulse.sqlite3')),
                      JSON_SORT_KEYS=False, TESTING=False)
    if test_config: app.config.update(test_config)
    os.makedirs(os.path.dirname(app.config['DATABASE']) or '.', exist_ok=True)
    init_db(app)
    app.extensions['metrics'] = Metrics()
    app.register_blueprint(api)
    @app.get('/')
    def index(): return render_template('index.html')
    @app.get('/health')
    def health(): return jsonify(status='ok', application='TriagePulse AI', mode='prototype')
    @app.errorhandler(404)
    def missing(_): return jsonify(error='not_found', message='The requested resource was not found.'), 404
    return app
