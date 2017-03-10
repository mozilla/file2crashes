# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import request, jsonify
from file2crashes import models, log


def crashes():
    product = request.args.get('product', 'Firefox')
    path = request.args.get('dir', '')
    date = request.args.get('date', 'today')
    log.info('Get crashes for {}, the {}: {}'.format(product, path, date))
    return jsonify(models.Crashes.get(product, 'nightly', path, date))


def listdirs():
    product = request.args.get('product', 'Firefox')
    date = request.args.get('date', 'today')
    log.info('List directories for {}, the {}'.format(product, date))
    return jsonify(models.Crashes.listdirs(product, 'nightly', date))


def dump():
    log.info('Dump')
    return jsonify(models.Crashes.dump())
