# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import six
import sys
from libmozdata import utils


def get_products():
    return ['Firefox', 'FennecAndroid']


def get_channels():
    return ['nightly', 'aurora', 'beta', 'release']


def disp(*args):
    print(args)
    sys.stdout.flush()


def get_date(date):
    if date:
        try:
            if isinstance(date, six.string_types):
                date = utils.get_date_ymd(date)
                return datetime.date(date.year, date.month, date.day)
            elif isinstance(date, datetime.date):
                return date
            elif isinstance(date, datetime.datetime):
                return datetime.date(date.year, date.month, date.day)
        except:
            pass
    return None


def get_correct_date(date):
    date = get_date(date)
    if date:
        return utils.get_date_str(date)
    return utils.get_date('today')


def get_correct_product(p):
    prods = {'firefox': 'Firefox',
             'fennecandroid': 'FennecAndroid'}
    return prods.get(p.lower(), 'Firefox')


def get_correct_channel(c):
    c = c.lower()
    return c if c in get_channels() else 'nightly'


def get_file(path):
    i = path.rfind('/')
    return path[:i], path[(i + 1):]
