# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import unittest

import flask

from test import helpers

from beachfront.services import users
from beachfront import middleware


class ApplyDefaultResponseHeadersTest(unittest.TestCase):
    def test_adds_correct_x_frame_options(self):
        response = flask.Response()
        middleware.apply_default_response_headers(response)
        self.assertEqual('DENY', response.headers['X-Frame-Options'])

    def test_adds_correct_x_content_type_options(self):
        response = flask.Response()
        middleware.apply_default_response_headers(response)
        self.assertEqual('nosniff', response.headers['X-Content-Type-Options'])

    def test_adds_correct_x_xss_protection(self):
        response = flask.Response()
        middleware.apply_default_response_headers(response)
        self.assertEqual('1; mode=block', response.headers['X-XSS-Protection'])

    def test_adds_correct_cache_control(self):
        response = flask.Response()
        middleware.apply_default_response_headers(response)
        self.assertEqual('no-cache, no-store, must-revalidate, private', response.headers['Cache-Control'])


class AuthFilterTest(helpers.MockableTestCase):
    def setUp(self):
        self.mock_authenticate = self.create_mock('beachfront.services.users.authenticate_via_api_key', side_effect=create_user)
        self.request = self.create_mock('flask.request', spec=flask.Request, authorization=None)
        self.session = self.create_mock('flask.session', new={})

    def test_checks_api_key_for_protected_endpoints(self):
        endpoints = (
            '/v0/services',
            '/v0/algorithm',
            '/v0/algorithm/test-service-id',
            '/v0/job',
            '/v0/job/test-job-id',
            '/v0/job/by_scene/test-scene-id',
            '/v0/job/by_productline/test-productline-id',
            '/v0/productline',
            '/random/path/somebody/maybe/forgot/to/protect',
        )
        for endpoint in endpoints:
            self.request.reset_mock()
            self.request.path = endpoint
            self.request.authorization = {'username': 'test-api-key'}
            middleware.auth_filter()
        self.assertEqual(len(endpoints), self.mock_authenticate.call_count)

    def test_allows_public_endpoints_to_pass_through(self):
        endpoints = (
            '/favicon.ico',
            '/login',
            '/login/callback',
            '/logout',
        )
        for endpoint in endpoints:
            self.request.reset_mock()
            self.request.path = endpoint
            middleware.auth_filter()
        self.assertEqual(0, self.mock_authenticate.call_count)

    def test_can_read_api_key_from_session(self):
        self.request.path = '/protected'
        self.request.authorization = None
        self.session['api_key'] = 'test-api-key-from-session'

        middleware.auth_filter()

        self.mock_authenticate.call_args.assert_called_once_with('test-api-key-from-session')

    def test_can_read_api_key_from_authorization_header(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key-from-auth-header'}

        middleware.auth_filter()

        self.mock_authenticate.call_args.assert_called_once_with('test-api-key-from-auth-header')

    def test_attaches_user_to_request(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}

        self.assertFalse(hasattr(self.request, 'user'))

        middleware.auth_filter()

        self.assertIsInstance(self.request.user, users.User)
        self.assertEqual('test-user-id', self.request.user.user_id)
        self.assertEqual('test-api-key', self.request.user.api_key)

    def test_rejects_if_api_key_is_missing(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': ''}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: API key is missing', 401), response)

    def test_rejects_if_api_key_is_malformed(self):
        self.mock_authenticate.side_effect = users.MalformedAPIKey()
        self.request.path = '/protected'
        self.request.authorization = {'username': 'lorem'}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: API key is malformed', 401), response)

    def test_rejects_when_api_key_is_not_active(self):
        self.mock_authenticate.side_effect = users.Unauthorized('negative ghost rider')
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}
        response = middleware.auth_filter()
        self.assertEqual(('Unauthorized: negative ghost rider', 401), response)

    def test_rejects_when_encountering_unexpected_verification_error(self):
        self.mock_authenticate.side_effect = users.Error('random error of known type')
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: an internal error prevents API key verification', 500), response)


class CSRFFilterTest(helpers.MockableTestCase):
    maxDiff = 4096

    def setUp(self):
        self.logger = helpers.get_logger('beachfront.middleware')
        self.request = self.create_mock('flask.request', spec=flask.Request,
                                        authorization={},
                                        headers={},
                                        method='POST',
                                        path='/v0/test-path',
                                        referrer='https://test-referrer.localdomain',
                                        remote_addr='1.2.3.4')
        self.session = self.create_mock('flask.session', new={})

    def tearDown(self):
        self.logger.destroy()

    def test_allows_when_method_is_rfc_2616_safe(self):
        self.session['api_key'] = 'test-api-key'

        for method in ('GET', 'OPTIONS', 'HEAD'):
            self.request.reset_mock()
            self.request.method = method
            response = middleware.csrf_filter()

            self.assertIsNone(response)

    def test_blocks_when_method_is_not_rfc_2616_safe(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'

        for method in ('POST', 'PUT', 'DELETE', 'PATCH', 'BISCUIT'):
            self.request.reset_mock()
            self.request.method = method

            response = middleware.csrf_filter()

            self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_allows_when_session_is_not_open(self):
        self.session.clear()

        response = middleware.csrf_filter()

        self.assertIsNone(response)

    def test_blocks_when_session_is_open(self):
        self.session['api_key'] = 'test-api-key'

        response = middleware.csrf_filter()

        self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_allows_when_csrf_token_header_is_correct(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'
        self.request.headers['X-XSRF-Token'] = 'test-csrf-token'

        response = middleware.csrf_filter()

        self.assertIsNone(response)

    def test_blocks_when_csrf_token_header_is_not_correct(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'
        self.request.headers['X-XSRF-Token'] = 'definitely not the token'

        response = middleware.csrf_filter()

        self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_blocks_when_csrf_token_header_is_blank(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'
        self.request.headers['X-XSRF-Token'] = ''

        response = middleware.csrf_filter()

        self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_blocks_when_csrf_token_header_is_absent(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'
        self.request.headers.clear()

        response = middleware.csrf_filter()

        self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_allows_when_api_key_is_present_and_well_formed(self):
        self.session['api_key'] = 'test-api-key'
        self.request.authorization = {'username': 'abcdef1234567890abcdef1234567890'}

        response = middleware.csrf_filter()

        self.assertIsNone(response)

    def test_blocks_when_api_key_is_present_and_malformed(self):
        self.session['api_key'] = 'test-api-key'
        self.request.authorization = {'username': 'totally malformed'}

        response = middleware.csrf_filter()

        self.assertEqual(('Access Denied: CSRF check failed', 403), response)

    def test_logs_rejections(self):
        self.session['api_key'] = 'test-api-key'
        self.session['csrf_token'] = 'test-csrf-token'
        self.request.headers['X-XSRF-Token'] = 'definitely not the token'
        self.request.headers['X-Requested-With'] = 'test-x-requested-with'
        self.request.headers['Origin'] = 'http://test-origin.localdomain'
        self.request.referrer = 'http://test-referrer.localdomain'

        middleware.csrf_filter()

        self.assertEqual([
            'WARNING - Possible CSRF attempt:',
            '---',
            '',
            'Path: /v0/test-path',
            '',
            'Origin: http://test-origin.localdomain',
            '',
            'Referrer: http://test-referrer.localdomain',
            '',
            'IP: 1.2.3.4',
            '',
            'X-Requested-With: test-x-requested-with',
            '',
            'X-CSRF-Token: definitely not the token',
            '',
            '---',
        ], self.logger.lines)


class HTTPSFilterTest(helpers.MockableTestCase):
    def setUp(self):
        self.logger = helpers.get_logger('beachfront.middleware')
        self.request = self.create_mock('flask.request',
                                        path='/test-path',
                                        referrer='http://test-referrer',
                                        is_secure=False)

    def tearDown(self):
        self.logger.destroy()

    def test_when_disabled_allows_https_requests(self):
        self.create_mock('beachfront.middleware.ENFORCE_HTTPS', new=False)
        self.request.is_secure = True

        response = middleware.https_filter()

        self.assertIsNone(response)

    def test_when_disabled_allows_non_https_requests(self):
        self.create_mock('beachfront.middleware.ENFORCE_HTTPS', new=False)
        self.request.is_secure = False

        response = middleware.https_filter()

        self.assertIsNone(response)

    def test_when_enabled_allows_https_requests(self):
        self.create_mock('beachfront.middleware.ENFORCE_HTTPS', new=True)
        self.request.is_secure = True

        response = middleware.https_filter()

        self.assertIsNone(response)

    def test_when_enabled_rejects_non_https_requests(self):
        self.create_mock('beachfront.middleware.ENFORCE_HTTPS', new=True)
        self.request.is_secure = False

        response = middleware.https_filter()

        self.assertEqual(('Access Denied: Please retry with HTTPS', 403), response)

    def test_logs_rejection(self):
        self.create_mock('beachfront.middleware.ENFORCE_HTTPS', new=True)
        self.request.is_secure = False

        middleware.https_filter()

        self.assertEqual([
            'WARNING - Rejecting non-HTTPS request: endpoint=`/test-path` referrer=`http://test-referrer`',
        ], self.logger.lines)


#
# Helpers
#

def create_user(api_key: str) -> users.User:
    return users.User(
        user_id='test-user-id',
        api_key=api_key,
        name='test-name',
    )
