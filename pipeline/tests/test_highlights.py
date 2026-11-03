"""Persistence and HTTP boundaries for saved text selections."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import uuid
from functools import partial
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve import Handler, RatingStore
from test_ratings import QuietHandler
import http.client


class HighlightsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'notes.sqlite3'
        self.store = RatingStore(self.path, {'eco', 'rax'})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, store=self.store))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.mark = dict(page='eco', id=str(uuid.uuid4()), start=4, end=9,
                         quote='机器人😀', prefix='正文', suffix=' context')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method, data=None, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        path = '/api/highlights' + ('?page=eco' if method == 'GET' else '')
        connection.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers)
        response = connection.getresponse()
        status, payload = response.status, json.loads(response.read())
        connection.close()
        return status, payload

    def test_persistence_duplicates_and_page_isolation(self):
        self.assertEqual(self.request('POST', self.mark)[0], 200)
        self.assertEqual(self.request('POST', self.mark)[0], 200)
        reopened = RatingStore(self.path, {'eco', 'rax'})
        self.assertEqual(len(reopened.read_highlights('eco')['highlights']), 1)
        self.assertEqual(reopened.read_highlights('rax')['highlights'], [])
        self.assertEqual(self.request('DELETE', self.mark)[0], 200)
        self.assertEqual(reopened.read_highlights('eco')['highlights'], [])

    def test_invalid_ranges_and_unknown_pages_do_not_write(self):
        for patch in ({'page': 'missing'}, {'start': -1}, {'end': 4}, {'end': 10},
                      {'quote': ''}, {'id': 'bad'}, {'start': True}, {'prefix': 'x' * 41}):
            with self.subTest(patch=patch):
                self.assertEqual(self.request('POST', {**self.mark, **patch})[0], 400)
        self.assertEqual(self.request('GET')[1]['highlights'], [])

    def test_ratings_are_preserved(self):
        self.store.write(dict(paper='eco', metric='influence', value=3))
        before = self.store.read()
        self.store.write_highlight(self.mark)
        self.store.delete_highlight(self.mark)
        self.assertEqual(before, self.store.read())

    def test_library_annotations(self):
        self.store.write_highlight({**self.mark, 'page': 'library'})
        self.assertEqual(len(self.store.read_highlights('library')['highlights']), 1)

    def test_cross_site_delete_is_rejected(self):
        self.request('POST', self.mark)
        self.assertEqual(self.request('DELETE', self.mark, 'https://other.example')[0], 403)
        self.assertEqual(len(self.request('GET')[1]['highlights']), 1)


if __name__ == '__main__':
    unittest.main()
