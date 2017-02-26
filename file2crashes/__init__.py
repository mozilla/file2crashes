# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Flask
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
import logging
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
log = logging.getLogger(__name__)


@app.route('/crashes', methods=['GET'])
@cross_origin()
def crashes():
    from file2crashes import api
    return api.crashes()


@app.route('/list', methods=['GET'])
@cross_origin()
def listdirs():
    from file2crashes import api
    return api.listdirs()


@app.route('/')
@app.route('/list.html')
def list_html():
    from file2crashes import html
    return html.listdirs()


@app.route('/crashes.html')
def crashes_html():
    from file2crashes import html
    return html.crashes()
