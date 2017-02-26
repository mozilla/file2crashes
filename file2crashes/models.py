# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import defaultdict
from file2crashes import utils as f2cutils
from file2crashes import app, db, analyze


class Crashes(db.Model):
    __tablename__ = 'crashes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product = db.Column(db.String(20))
    channel = db.Column(db.String(20))
    date = db.Column(db.Date)
    directory = db.Column(db.String(256))
    file = db.Column(db.String(128))
    url = db.Column(db.Text)
    count = db.Column(db.Integer, default=0)
    signature = db.Column(db.String(512))

    def __init__(self, product, channel, date, path, url, count, signature):
        self.product = product
        self.channel = channel
        self.date = f2cutils.get_date(date)
        self.directory, self.file = f2cutils.get_file(path)
        self.url = url
        self.count = count
        self.signature = signature

    @staticmethod
    def put(product, channel, date, file, url, count, signature, commit=True):
        c = db.session.query(Crashes).filter_by(product=product,
                                                channel=channel,
                                                date=date,
                                                file=file,
                                                url=url)
        if c.first():
            c = c.first()
            c.count = count
        else:
            c = Crashes(product, channel, date, file, url, count, signature)

        db.session.add(c)

        if commit:
            db.session.commit()

    @staticmethod
    def put_data(data, date, commit=True):
        if data:
            for channel, info1 in data.items():
                for product, info2 in info1.items():
                    for file, url_count in info2.items():
                        for v in url_count:
                            Crashes.put(product,
                                        channel,
                                        date,
                                        file,
                                        v['url'],
                                        v['count'],
                                        v['signature'],
                                        commit=False)

            if commit:
                db.session.commit()

            return True
        return False

    @staticmethod
    def get(product, channel, directory, date):
        if directory:
            date = f2cutils.get_date(date)
            if date:
                cs = db.session.query(Crashes).filter_by(product=product,
                                                         channel=channel,
                                                         date=date,
                                                         directory=directory)
            r = defaultdict(lambda: list())
            for c in cs:
                r[c.file].append([c.url, c.count, c.signature])

            return {f: sorted(u, key=lambda p: p[1]) for f, u in r.items()}

        return {}

    @staticmethod
    def listdirs(product, channel, date):
        cs = db.session.query(Crashes).filter_by(product=product,
                                                 channel=channel,
                                                 date=date)
        dirs = set(c.directory for c in cs)
        dirs = list(sorted(dirs))

        return dirs


def update(date='today'):
    results = analyze.get(['nightly'],
                          ['Firefox', 'FennecAndroid'],
                          date=date)
    Crashes.put_data(results, date)


def create():
    engine = db.get_engine(app)
    if not engine.dialect.has_table(engine, 'crashes'):
        db.create_all()
        update()
