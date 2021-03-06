# -*- coding: utf-8 -*-

import json
from mock import Mock
from urlparse import ParseResult
from searx import webapp
from searx.testing import SearxTestCase


class ViewsTestCase(SearxTestCase):

    def setUp(self):
        webapp.app.config['TESTING'] = True  # to get better error messages
        self.app = webapp.app.test_client()
        webapp.default_theme = 'default'

        # set some defaults
        self.test_results = [
            {
                'content': 'first test content',
                'title': 'First Test',
                'url': 'http://first.test.xyz',
                'engines': ['youtube', 'startpage'],
                'engine': 'startpage',
                'parsed_url': ParseResult(scheme='http', netloc='first.test.xyz', path='/', params='', query='', fragment=''),  # noqa
            }, {
                'content': 'second test content',
                'title': 'Second Test',
                'url': 'http://second.test.xyz',
                'engines': ['youtube', 'startpage'],
                'engine': 'youtube',
                'parsed_url': ParseResult(scheme='http', netloc='second.test.xyz', path='/', params='', query='', fragment=''),  # noqa
            },
        ]

        def search_mock(search_self, *args):
            search_self.result_container = Mock(get_ordered_results=lambda: self.test_results,
                                                answers=set(),
                                                suggestions=set(),
                                                infoboxes=[],
                                                results=self.test_results,
                                                results_length=lambda: len(self.test_results))

        webapp.Search.search = search_mock

        self.maxDiff = None  # to see full diffs

    def test_index_empty(self):
        result = self.app.post('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<div class="title"><h1>searx</h1></div>', result.data)

    def test_index_html(self):
        result = self.app.post('/', data={'q': 'test'})
        self.assertIn(
            '<h3 class="result_title"><img width="14" height="14" class="favicon" src="/static/themes/default/img/icons/icon_youtube.ico" alt="youtube" /><a href="http://second.test.xyz" rel="noreferrer">Second <span class="highlight">Test</span></a></h3>',  # noqa
            result.data
        )
        self.assertIn(
            '<p class="content">first <span class="highlight">test</span> content<br class="last"/></p>',  # noqa
            result.data
        )

    def test_index_json(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'json'})

        result_dict = json.loads(result.data)

        self.assertEqual('test', result_dict['query'])
        self.assertEqual(
            result_dict['results'][0]['content'], 'first test content')
        self.assertEqual(
            result_dict['results'][0]['url'], 'http://first.test.xyz')

    def test_index_csv(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'csv'})

        self.assertEqual(
            'title,url,content,host,engine,score\r\n'
            'First Test,http://first.test.xyz,first test content,first.test.xyz,startpage,\r\n'  # noqa
            'Second Test,http://second.test.xyz,second test content,second.test.xyz,youtube,\r\n',  # noqa
            result.data
        )

    def test_index_rss(self):
        result = self.app.post('/', data={'q': 'test', 'format': 'rss'})

        self.assertIn(
            '<description>Search results for "test" - searx</description>',
            result.data
        )

        self.assertIn(
            '<opensearch:totalResults>2</opensearch:totalResults>',
            result.data
        )

        self.assertIn(
            '<title>First Test</title>',
            result.data
        )

        self.assertIn(
            '<link>http://first.test.xyz</link>',
            result.data
        )

        self.assertIn(
            '<description>first test content</description>',
            result.data
        )

    def test_about(self):
        result = self.app.get('/about')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h1>About <a href="/">searx</a></h1>', result.data)

    def test_preferences(self):
        result = self.app.get('/preferences')
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            '<form method="post" action="/preferences" id="search_form">',
            result.data
        )
        self.assertIn(
            '<legend>Default categories</legend>',
            result.data
        )
        self.assertIn(
            '<legend>Interface language</legend>',
            result.data
        )

    def test_stats(self):
        result = self.app.get('/stats')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h2>Engine stats</h2>', result.data)

    def test_robots_txt(self):
        result = self.app.get('/robots.txt')
        self.assertEqual(result.status_code, 200)
        self.assertIn('Allow: /', result.data)

    def test_opensearch_xml(self):
        result = self.app.get('/opensearch.xml')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<Description>a privacy-respecting, hackable metasearch engine</Description>', result.data)

    def test_favicon(self):
        result = self.app.get('/favicon.ico')
        self.assertEqual(result.status_code, 200)
