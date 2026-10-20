#!/usr/bin/env python3
"""Serve the local paper library and persist personal ratings in SQLite."""
import argparse
import json
import sqlite3
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
METRICS = {'influence', 'experiments', 'reference'}


class RatingStore:
    def __init__(self, path, papers):
        self.path = Path(path)
        self.papers = set(papers)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS ratings (
                paper TEXT NOT NULL, metric TEXT NOT NULL,
                value INTEGER NOT NULL CHECK(value BETWEEN 0 AND 5),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(paper, metric))''')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def validate(self, entry):
        if not isinstance(entry, dict):
            raise ValueError('评分格式错误')
        paper, metric, value = (entry.get(k) for k in ('paper', 'metric', 'value'))
        if not isinstance(paper, str) or paper not in self.papers:
            raise ValueError('未知论文')
        if not isinstance(metric, str) or metric not in METRICS:
            raise ValueError('未知评分项目')
        if type(value) is not int or not 0 <= value <= 5:
            raise ValueError('评分必须为 0 到 5 的整数')
        return paper, metric, value

    def read(self):
        result = {}
        with self.connect() as db:
            for paper, metric, value in db.execute('SELECT paper, metric, value FROM ratings'):
                result.setdefault(paper, {})[metric] = value
        return {'ratings': result}

    def write(self, entry):
        values = self.validate(entry)
        with self.connect() as db:
            db.execute('''INSERT INTO ratings(paper,metric,value) VALUES(?,?,?)
                ON CONFLICT(paper,metric) DO UPDATE SET
                value=excluded.value, updated_at=CURRENT_TIMESTAMP''', values)
        return {'saved': True, **dict(zip(('paper', 'metric', 'value'), values))}

    def import_missing(self, entries):
        if not isinstance(entries, list) or len(entries) > len(self.papers) * len(METRICS):
            raise ValueError('迁移评分格式错误')
        values = [self.validate(entry) for entry in entries]
        with self.connect() as db:
            db.executemany('INSERT OR IGNORE INTO ratings(paper,metric,value) VALUES(?,?,?)', values)
        return self.read()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, store, **kwargs):
        self.store = store
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def valid_host(self):
        return self.headers.get('Host') in {
            f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def json_response(self, code, data, head=False):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def static_allowed(self):
        path = unquote(urlsplit(self.path).path)
        parts = Path(path).parts
        return (path == '/' or (len(parts) > 1 and parts[1] in {'site', 'sources'})) and not any(
            part.startswith('.') or part == '..' for part in parts if part != '/')

    def do_GET(self):
        if not self.valid_host():
            return self.json_response(403, {'error': '仅允许本机访问'})
        path = urlsplit(self.path).path
        if path == '/api/ratings':
            try:
                return self.json_response(200, self.store.read())
            except sqlite3.Error:
                return self.json_response(500, {'error': '数据库读取失败'})
        if path.startswith('/api/') or not self.static_allowed():
            return self.json_response(404, {'error': '未找到页面'})
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/site/index.html')
            self.end_headers()
            return
        return super().do_GET()

    def do_HEAD(self):
        if not self.valid_host() or not self.static_allowed():
            return self.json_response(404, {'error': '未找到页面'}, head=True)
        return super().do_HEAD()

    def mutation(self, importing=False):
        if not self.valid_host():
            return self.json_response(403, {'error': '仅允许本机访问'})
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers['Host']:
            return self.json_response(403, {'error': '不允许跨站修改评分'})
        expected = '/api/ratings/import' if importing else '/api/ratings'
        if urlsplit(self.path).path != expected:
            return self.json_response(404, {'error': '未找到接口'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.json_response(415, {'error': '请求需要使用 JSON 格式'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('请求大小错误')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('评分格式错误')
            result = self.store.import_missing(data.get('ratings')) if importing else self.store.write(data)
        except (ValueError, UnicodeError):
            return self.json_response(400, {'error': '评分内容无效，请使用已有论文、评分项目和 0 到 5 的整数'})
        except sqlite3.Error:
            return self.json_response(500, {'error': '数据库写入失败，评分未保存'})
        return self.json_response(200, result)

    def do_PUT(self):
        self.mutation()

    def do_POST(self):
        self.mutation(importing=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--db', type=Path, default=ROOT / '_data/ratings.sqlite3')
    args = parser.parse_args()
    papers = json.loads((ROOT / 'content/reading-reviews.json').read_text())['papers']
    store = RatingStore(args.db, papers)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, store=store))
    print(f'阅读与评分：http://127.0.0.1:{args.port}/site/index.html\n评分数据库：{args.db}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
