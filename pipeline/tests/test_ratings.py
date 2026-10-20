"""Persistence, migration and HTTP validation for the local rating service."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve import Handler, RatingStore


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class RatingsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'ratings.sqlite3'
        self.store = RatingStore(self.path, {'rax', 'bcg'})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, store=self.store))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method, path='/api/ratings', data=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        body = json.dumps(data) if data is not None else None
        connection.request(method, path, body=body, headers=headers or {'Content-Type': 'application/json'})
        response = connection.getresponse()
        status, payload = response.status, response.read()
        connection.close()
        return status, json.loads(payload)

    def test_save_clear_and_reopen_database(self):
        entry = dict(paper='rax', metric='influence', value=4)
        self.assertEqual(self.request('PUT', data=entry)[0], 200)
        reopened = RatingStore(self.path, {'rax', 'bcg'})
        self.assertEqual(reopened.read()['ratings']['rax']['influence'], 4)
        self.assertEqual(self.request('GET')[1]['ratings']['rax']['influence'], 4)
        entry['value'] = 0
        self.assertEqual(self.request('PUT', data=entry)[0], 200)
        self.assertEqual(reopened.read()['ratings']['rax']['influence'], 0)

    def test_migration_never_overwrites_existing_or_cleared_scores(self):
        self.store.write(dict(paper='rax', metric='influence', value=0))
        entries = [dict(paper='rax', metric='influence', value=5),
                   dict(paper='bcg', metric='reference', value=3)]
        for _ in range(2):
            status, data = self.request('POST', '/api/ratings/import', {'ratings': entries})
            self.assertEqual(status, 200)
            self.assertEqual(data['ratings']['rax']['influence'], 0)
            self.assertEqual(data['ratings']['bcg']['reference'], 3)

    def test_invalid_ratings_do_not_write(self):
        for value in (-1, 6, True, '4', None):
            self.assertEqual(self.request('PUT', data=dict(paper='rax', metric='influence', value=value))[0], 400)
        self.assertEqual(self.request('PUT', data=dict(paper='unknown', metric='influence', value=4))[0], 400)
        self.assertEqual(self.request('PUT', data=dict(paper='rax', metric='other', value=4))[0], 400)
        entries = [dict(paper='rax', metric='influence', value=4), dict(paper='bcg', metric='reference', value=99)]
        self.assertEqual(self.request('POST', '/api/ratings/import', {'ratings': entries})[0], 400)
        self.assertEqual(self.store.read()['ratings'], {})

    def test_database_is_not_served_and_cross_site_writes_rejected(self):
        for path in ('/_data/ratings.sqlite3', '/site/../_data/ratings.sqlite3', '/.git/config'):
            self.assertEqual(self.request('GET', path)[0], 404)
        entry = dict(paper='rax', metric='influence', value=4)
        self.assertEqual(self.request('PUT', data=entry, headers={
            'Content-Type': 'application/json', 'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('PUT', data=entry, headers={'Content-Type': 'text/plain'})[0], 415)


if __name__ == '__main__':
    unittest.main()
