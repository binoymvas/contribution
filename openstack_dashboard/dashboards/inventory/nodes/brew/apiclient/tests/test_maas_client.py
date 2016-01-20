# Copyright 2012-2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test MAAS HTTP API client."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import gzip
from io import BytesIO
import json
from random import randint
import urllib2
from urlparse import (
    parse_qs,
    urljoin,
    urlparse,
)

from apiclient.maas_client import (
    MAASClient,
    MAASDispatcher,
    MAASOAuth,
)
from apiclient.testing.django import (
    parse_headers_and_body_with_django,
    parse_headers_and_body_with_mimer,
)
from maastesting.factory import factory
from maastesting.fixtures import TempWDFixture
from maastesting.httpd import HTTPServerFixture
from maastesting.testcase import MAASTestCase
from testtools.matchers import (
    AfterPreprocessing,
    Equals,
    MatchesListwise,
)


class TestMAASOAuth(MAASTestCase):

    def test_sign_request_adds_header(self):
        headers = {}
        auth = MAASOAuth('consumer_key', 'resource_token', 'resource_secret')
        auth.sign_request('http://example.com/', headers)
        self.assertIn('Authorization', headers)


class TestMAASDispatcher(MAASTestCase):

    def test_dispatch_query_makes_direct_call(self):
        contents = factory.make_string()
        url = "file://%s" % self.make_file(contents=contents)
        self.assertEqual(
            contents, MAASDispatcher().dispatch_query(url, {}).read())

    def test_request_from_http(self):
        # We can't just call self.make_file because HTTPServerFixture will only
        # serve content from the current WD. And we don't want to create random
        # content in the original WD.
        self.useFixture(TempWDFixture())
        name = factory.make_string()
        content = factory.make_string().encode('ascii')
        factory.make_file(location='.', name=name, contents=content)
        with HTTPServerFixture() as httpd:
            url = urljoin(httpd.url, name)
            response = MAASDispatcher().dispatch_query(url, {})
            self.assertEqual(200, response.code)
            self.assertEqual(content, response.read())

    def test_supports_any_method(self):
        # urllib2, which MAASDispatcher uses, only supports POST and
        # GET. There is some extra code that makes sure the passed
        # method is honoured which is tested here.
        self.useFixture(TempWDFixture())
        name = factory.make_string()
        content = factory.make_string(300).encode('ascii')
        factory.make_file(location='.', name=name, contents=content)

        method = "PUT"
        # The test httpd doesn't like PUT, so we'll look for it bitching
        # about that for the purposes of this test.
        with HTTPServerFixture() as httpd:
            url = urljoin(httpd.url, name)
            e = self.assertRaises(
                urllib2.HTTPError, MAASDispatcher().dispatch_query, url, {},
                method=method)
            self.assertIn("Unsupported method ('PUT')", e.reason)

    def test_supports_content_encoding_gzip(self):
        # The client will set the Accept-Encoding: gzip header, and it will
        # also decompress the response if it comes back with Content-Encoding:
        # gzip.
        self.useFixture(TempWDFixture())
        name = factory.make_string()
        content = factory.make_string(300).encode('ascii')
        factory.make_file(location='.', name=name, contents=content)
        called = []
        orig_urllib = urllib2.urlopen

        def logging_urlopen(*args, **kwargs):
            called.append((args, kwargs))
            return orig_urllib(*args, **kwargs)
        self.patch(urllib2, 'urlopen', logging_urlopen)
        with HTTPServerFixture() as httpd:
            url = urljoin(httpd.url, name)
            res = MAASDispatcher().dispatch_query(url, {})
            self.assertEqual(200, res.code)
            self.assertEqual(content, res.read())
        request = called[0][0][0]
        self.assertEqual([((request,), {})], called)
        self.assertEqual('gzip', request.headers.get('Accept-encoding'))

    def test_doesnt_override_accept_encoding_headers(self):
        # If someone passes their own Accept-Encoding header, then dispatch
        # just passes it through.
        self.useFixture(TempWDFixture())
        name = factory.make_string()
        content = factory.make_string(300).encode('ascii')
        factory.make_file(location='.', name=name, contents=content)
        with HTTPServerFixture() as httpd:
            url = urljoin(httpd.url, name)
            headers = {'Accept-encoding': 'gzip'}
            res = MAASDispatcher().dispatch_query(url, headers)
            self.assertEqual(200, res.code)
            self.assertEqual('gzip', res.info().get('Content-Encoding'))
            raw_content = res.read()
        read_content = gzip.GzipFile(
            mode='rb', fileobj=BytesIO(raw_content)).read()
        self.assertEqual(content, read_content)


def make_path():
    """Create an arbitrary resource path."""
    return "/" + '/'.join(factory.make_string() for counter in range(2))


class FakeDispatcher:
    """Fake MAASDispatcher.  Records last invocation, returns given result."""

    last_call = None

    def __init__(self, result=None):
        self.result = result

    def dispatch_query(self, request_url, headers, method=None, data=None):
        self.last_call = {
            'request_url': request_url,
            'headers': headers,
            'method': method,
            'data': data,
        }
        return self.result


def make_client(root=None, result=None):
    """Create a MAASClient."""
    if root is None:
        root = factory.make_simple_http_url(
            path=factory.make_name("path") + "/")
    auth = MAASOAuth(
        factory.make_string(), factory.make_string(),
        factory.make_string())
    return MAASClient(auth, FakeDispatcher(result=result), root)


class TestMAASClient(MAASTestCase):

    def test_make_url_joins_root_and_path(self):
        path = make_path()
        client = make_client()
        expected = client.url.rstrip("/") + "/" + path.lstrip("/")
        self.assertEqual(expected, client._make_url(path))

    def test_make_url_converts_sequence_to_path(self):
        path = ['top', 'sub', 'leaf']
        client = make_client(root='http://example.com/')
        self.assertEqual(
            'http://example.com/top/sub/leaf', client._make_url(path))

    def test_make_url_represents_path_components_as_text(self):
        number = randint(0, 100)
        client = make_client()
        self.assertEqual(
            urljoin(client.url, unicode(number)), client._make_url([number]))

    def test_formulate_get_makes_url(self):
        path = make_path()
        client = make_client()
        url, headers = client._formulate_get(path)
        expected = client.url.rstrip("/") + "/" + path.lstrip("/")
        self.assertEqual(expected, url)

    def test_formulate_get_adds_parameters_to_url(self):
        params = {
            factory.make_string(): factory.make_string()
            for counter in range(3)}
        url, headers = make_client()._formulate_get(make_path(), params)
        expectation = {key: [value] for key, value in params.items()}
        self.assertEqual(expectation, parse_qs(urlparse(url).query))

    def test_formulate_get_adds_list_parameters_to_url(self):
        params = {
            factory.make_string(): [
                factory.make_string() for _ in range(2)],
            factory.make_string(): [
                factory.make_string() for _ in range(2)]
        }
        k = params.keys()
        v = [value for values in params.values() for value in values]
        url, headers = make_client()._formulate_get(make_path(), params)
        url_args = url.split('?')[1]
        self.assertEqual(
            "%s=%s&%s=%s&%s=%s&%s=%s" %
            (k[0], v[0], k[0], v[1], k[1], v[2], k[1], v[3]),
            url_args)

    def test_flatten_flattens_out_list(self):
        number = randint(0, 10)
        key = factory.make_string()
        param_list = [factory.make_string() for counter in range(number)]
        params = {key: param_list}
        flattend_list = list(make_client()._flatten(params))
        expectation = [(key, value) for value in param_list]
        self.assertEqual(expectation, flattend_list)

    def test_formulate_get_signs_request(self):
        url, headers = make_client()._formulate_get(make_path())
        self.assertIn('Authorization', headers)

    def test_formulate_change_makes_url(self):
        path = make_path()
        client = make_client()
        url, headers, body = client._formulate_change(path, {})
        expected = client.url.rstrip("/") + "/" + path.lstrip("/")
        self.assertEqual(expected, url)

    def test_formulate_change_signs_request(self):
        url, headers, body = make_client()._formulate_change(make_path(), {})
        self.assertIn('Authorization', headers)

    def test_formulate_change_passes_parameters_in_body(self):
        params = {factory.make_string(): factory.make_string()}
        url, headers, body = make_client()._formulate_change(
            make_path(), params)
        post, _ = parse_headers_and_body_with_django(headers, body)
        self.assertEqual(
            {name: [value] for name, value in params.items()}, post)

    def test_formulate_change_as_json(self):
        params = {factory.make_string(): factory.make_string()}
        url, headers, body = make_client()._formulate_change(
            make_path(), params, as_json=True)
        observed = [
            headers.get('Content-Type'),
            headers.get('Content-Length'),
            body,
            ]
        expected = [
            Equals('application/json'),
            Equals('%d' % (len(body),)),
            AfterPreprocessing(json.loads, Equals(params)),
            ]
        self.assertThat(observed, MatchesListwise(expected))
        data = parse_headers_and_body_with_mimer(headers, body)
        self.assertEqual(params, data)

    def test_get_dispatches_to_resource(self):
        path = make_path()
        client = make_client()
        client.get(path)
        request = client.dispatcher.last_call
        self.assertEqual(client._make_url(path), request['request_url'])
        self.assertIn('Authorization', request['headers'])
        self.assertEqual('GET', request['method'])
        self.assertIsNone(request['data'])

    def test_get_without_op_gets_simple_resource(self):
        expected_result = factory.make_string()
        client = make_client(result=expected_result)
        result = client.get(make_path())
        self.assertEqual(expected_result, result)

    def test_get_with_op_queries_resource(self):
        path = make_path()
        method = factory.make_string()
        client = make_client()
        client.get(path, method)
        dispatch = client.dispatcher.last_call
        self.assertEqual(
            client._make_url(path) + '?op=%s' % method,
            dispatch['request_url'])

    def test_get_passes_parameters(self):
        path = make_path()
        param = factory.make_string()
        method = factory.make_string()
        client = make_client()
        client.get(path, method, parameter=param)
        request = client.dispatcher.last_call
        self.assertIsNone(request['data'])
        query = parse_qs(urlparse(request['request_url']).query)
        self.assertItemsEqual([param], query['parameter'])

    def test_post_dispatches_to_resource(self):
        path = make_path()
        client = make_client()
        method = factory.make_string()
        client.post(path, method)
        request = client.dispatcher.last_call
        self.assertEqual(client._make_url(path) + "?op=%s" % (method,),
                         request['request_url'])
        self.assertIn('Authorization', request['headers'])
        self.assertEqual('POST', request['method'])

    def test_post_passes_parameters(self):
        param = factory.make_string()
        method = factory.make_string()
        client = make_client()
        client.post(make_path(), method, parameter=param)
        request = client.dispatcher.last_call
        post, _ = parse_headers_and_body_with_django(
            request["headers"], request["data"])
        self.assertTrue(request["request_url"].endswith('?op=%s' % (method,)))
        self.assertEqual({"parameter": [param]}, post)

    def test_post_as_json(self):
        param = factory.make_string()
        method = factory.make_string()
        list_param = [factory.make_string() for _ in range(10)]
        client = make_client()
        client.post(make_path(), method, as_json=True,
                    param=param, list_param=list_param)
        request = client.dispatcher.last_call
        self.assertEqual('application/json',
                         request['headers'].get('Content-Type'))
        content = parse_headers_and_body_with_mimer(
            request['headers'], request['data'])
        self.assertTrue(request["request_url"].endswith('?op=%s' % (method,)))
        self.assertEqual({'param': param, 'list_param': list_param}, content)

    def test_put_dispatches_to_resource(self):
        path = make_path()
        client = make_client()
        client.put(path, parameter=factory.make_string())
        request = client.dispatcher.last_call
        self.assertEqual(client._make_url(path), request['request_url'])
        self.assertIn('Authorization', request['headers'])
        self.assertEqual('PUT', request['method'])

    def test_delete_dispatches_to_resource(self):
        path = make_path()
        client = make_client()
        client.delete(path)
        request = client.dispatcher.last_call
        self.assertEqual(client._make_url(path), request['request_url'])
        self.assertIn('Authorization', request['headers'])
        self.assertEqual('DELETE', request['method'])

    def test_delete_passes_body(self):
        # A DELETE request should have an empty body.  But we can't just leave
        # the body out altogether, or the request will hang (bug 1313556).
        client = make_client()
        client.delete(make_path())
        self.assertIsNotNone(client.dispatcher.last_call['data'])
