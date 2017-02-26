# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from file2crashes import utils, models
from flask import request, render_template
from requests.utils import quote


def listdirs():
    product = request.args.get('product', '')
    product = utils.get_correct_product(product)
    date = request.args.get('date', 'today')
    date = utils.get_correct_date(date)
    channel = 'nightly'
    dirs = models.Crashes.listdirs(product, channel, date)
    url = 'crashes.html?product={}&channel={}&date={}&dir='.format(product,
                                                                   channel,
                                                                   date)
    return render_template('list.html',
                           quote=quote,
                           base_url=url,
                           dirs=dirs)


def crashes():
    product = request.args.get('product', '')
    product = utils.get_correct_product(product)
    date = request.args.get('date', 'today')
    date = utils.get_correct_date(date)
    directory = request.args.get('dir', '')
    channel = 'nightly'
    crashes = models.Crashes.get(product, channel, directory, date)

    def plural(n):
        return 'crash' if n == 1 else 'crashes'

    return render_template('crashes.html',
                           plural=plural,
                           sortfun=sorted,
                           crashes=crashes)
