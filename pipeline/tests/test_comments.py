"""User-written comments persist independently of ratings and highlights."""
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
from serve import RatingStore
from test_ratings import QuietHandler


class CommentsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'comments.sqlite3'
        self.store = RatingStore(self.path, {'eco', 'rax'})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, store=self.store))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

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
        connection.request(method, '/api/comments', body=json.dumps(data) if data is not None else None, headers=headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_save_edit_clear_and_reopen(self):
        for text in ('方法值得借鉴。\n再核对实验 😀', '<b>保留为纯文本</b>', ''):
            self.assertEqual(self.request('PUT', {'paper': 'eco', 'text': text})[0], 200)
            self.assertEqual(self.request('GET')[1]['comments']['eco'], text)
            reopened = RatingStore(self.path, {'eco', 'rax'})
            self.assertEqual(reopened.read_comments()['comments']['eco'], text)
        self.assertNotIn('rax', self.request('GET')[1]['comments'])

    def test_invalid_input_does_not_write(self):
        for entry in (None, [], {'paper': 'missing', 'text': '评语'}, {'paper': 'eco', 'text': 2},
                      {'paper': 'eco', 'text': '字' * 5001}):
            with self.subTest(entry=type(entry)):
                self.assertEqual(self.request('PUT', entry)[0], 400)
        self.assertEqual(self.request('GET')[1]['comments'], {})

    def test_cross_site_write_does_not_replace_comment(self):
        self.store.write_comment({'paper': 'eco', 'text': '我的评语'})
        status, _ = self.request('PUT', {'paper': 'eco', 'text': '替换'}, 'https://other.example')
        self.assertEqual(status, 403)
        self.assertEqual(self.store.read_comments()['comments']['eco'], '我的评语')

    def test_ratings_are_preserved(self):
        self.store.write({'paper': 'eco', 'metric': 'influence', 'value': 4})
        before = self.store.read()
        self.store.write_comment({'paper': 'eco', 'text': '评语'})
        self.assertEqual(self.store.read(), before)


if __name__ == '__main__':
    unittest.main()
