# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
from datetime import timedelta
import re
import copy
from collections import defaultdict
from libmozdata import socorro
from libmozdata import utils
from libmozdata.connection import (Connection, Query)


hg_pattern = re.compile('hg:hg.mozilla.org[^:]*:([^:]*):([a-z0-9]+)')
forbidden_dirs = {'obj-firefox'}


def is_allowed(name):
    return all(not name.startswith(d) for d in forbidden_dirs)


def get_file(hg_uri):
    """Get node for file name from path

    Args:
        path (str): path from socorro

    Returns:
        (str, str): filename and node
    """
    if hg_uri:
        m = hg_pattern.match(hg_uri)
        if m:
            f = m.group(1)
            if is_allowed(f):
                return f

    return ''


def get_files(info, verbose=False):
    """Get info from different backtraces

    Args:
        info (dict): proto -> uuid

    Returns:
        dict: info about the different backtraces
    """

    def handler(proto, json, data):
        jd = json['json_dump']
        if 'threads' in jd and 'crashedThread' in json:
            thread_nb = json['crashedThread']
            if thread_nb is not None:
                frames = jd['threads'][thread_nb]['frames']
                data[proto] = set(map(lambda f: get_file(f['file']),
                                      filter(lambda f: 'file' in f,
                                             frames)))

    data = {}
    queries = []

    for proto, value in info.items():
        queries.append(Query(socorro.ProcessedCrash.URL,
                             params={'crash_id': value['uuid']},
                             handler=functools.partial(handler, proto),
                             handlerdata=data))

    if queries:
        socorro.ProcessedCrash(queries=queries).wait()

    return data


def get_new_signatures(data, threshold=0):
    new_signatures = []
    for sgn, stats in data.items():
        stats = sorted(stats.items(), key=lambda p: p[0])
        numbers = [n for _, n in stats]
        if all(i == 0 for i in numbers[:-1]) and numbers[-1] >= threshold:
            new_signatures.append(sgn)
    return sorted(new_signatures)


def get_uuids(channel,
              product='Firefox',
              date='today',
              limit=10000,
              max_days=3,
              threshold=5):
    end_date = utils.get_date_ymd(date)
    start_date = end_date - timedelta(days=max_days + 1)
    search_date = socorro.SuperSearch.get_search_date(start_date, end_date)

    r = range(max_days + 1)
    default_trend = {start_date + timedelta(days=i): 0 for i in r}
    data = defaultdict(lambda: copy.deepcopy(default_trend))

    def handler(json, data):
        if not json['errors']:
            for facets in json['facets']['histogram_date']:
                d = utils.get_date_ymd(facets['term'])
                s = facets['facets']['signature']
                for signature in s:
                    count = signature['count']
                    sgn = signature['term']
                    data[sgn][d] += count

    socorro.SuperSearch(params={'product': product,
                                'date': search_date,
                                'release_channel': channel,
                                '_histogram.date': 'signature',
                                '_facets_size': limit,
                                '_results_number': 1},
                        handler=handler, handlerdata=data).wait()

    new_signatures = get_new_signatures(data, threshold=threshold)

    if new_signatures:
        data = {}
        queries = []

        def handler(json, data):
            if not json['errors']:
                for facets in json['facets']['proto_signature']:
                    proto = facets['term']
                    count = facets['count']
                    facets = facets['facets']
                    signature = facets['signature'][0]['term']
                    first_uuid = facets['uuid'][0]['term']
                    data[proto] = {'uuid': first_uuid,
                                   'count': count,
                                   'signature': signature}

        for sgns in Connection.chunks(new_signatures, 5):
            queries.append(Query(socorro.SuperSearch.URL,
                                 {'product': product,
                                  'date': search_date,
                                  'signature': ['=' + s for s in sgns],
                                  'release_channel': channel,
                                  '_aggs.proto_signature': ['uuid',
                                                            'signature'],
                                  '_facets_size': 1000,
                                  '_results_number': 0},
                                 handler=handler, handlerdata=data))

        socorro.SuperSearch(queries=queries).wait()
        return data, search_date

    return {}, ''


def get(channels,
        products,
        date='today',
        limit=10000,
        max_days=3,
        threshold=0,
        verbose=False):
    results = defaultdict(lambda: dict())
    for channel in channels:
        for product in products:
            protos, search_date = get_uuids(channel,
                                            product=product,
                                            date=date,
                                            limit=limit,
                                            max_days=max_days,
                                            threshold=threshold)
            if protos:
                interesting = defaultdict(lambda: [])
                pf = get_files(protos, verbose=verbose)
                for proto, files in pf.items():
                    for f in filter(lambda f: f is not '', files):
                        params = {'release_channel': channel,
                                  'product': product,
                                  'date': search_date,
                                  'proto_signature': '=' + proto}
                        url = socorro.SuperSearch.get_link(params)
                        p = protos[proto]
                        interesting[f].append({'url': url,
                                               'count': p['count'],
                                               'signature': p['signature']})
                results[channel][product] = dict(interesting)

    return dict(results)
