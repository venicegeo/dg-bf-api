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

from test import helpers

from beachfront import routes
from beachfront.services import users
from beachfront.utils import geoaxis


class LoginTest(helpers.MockableTestCase):
    def test_renders_login_page(self):
        mock_render = self.create_mock('flask.render_template', return_value='test-rendered-template')
        self.create_mock('beachfront.services.users.create_oauth_url', return_value='test-oauth-url')

        response = routes.login()

        self.assertEqual('test-rendered-template', response)
        mock_render.assert_called_once_with('login.jinja2', oauth_url='test-oauth-url')


class LoginCallbackTest(helpers.MockableTestCase):
    def setUp(self):
        self.mock_authenticate = self.create_mock('beachfront.services.users.authenticate_via_geoaxis', return_value=None)
        self.mock_redirect = self.create_mock('flask.redirect')
        self.mock_url_for = self.create_mock('flask.url_for', side_effect=lambda s: 'test-url-for-{}'.format(s))
        self.request = self.create_mock('flask.request', path='/login', args={})
        self.session = self.create_mock('flask.session', new=MockSession())

    def test_rejects_when_auth_code_is_missing(self):
        self.request.args = {}

        response = routes.login_callback()

        self.assertEqual(('Cannot log in: invalid "code" query parameter', 400), response)

    def test_rejects_when_auth_code_is_blank(self):
        self.request.args = {'code': ''}

        response = routes.login_callback()

        self.assertEqual(('Cannot log in: invalid "code" query parameter', 400), response)

    def test_passes_correct_auth_code_to_users_service(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        routes.login_callback()

        self.mock_authenticate.assert_called_once_with('test-auth-code')

    def test_attaches_api_key_to_session_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        routes.login_callback()

        self.assertEqual('test-api-key', self.session['api_key'])

    def test_attaches_csrf_token_to_session_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        routes.login_callback()

        self.assertRegex(self.session['csrf_token'], r'^[0-9a-f]{64}$')

    def test_sets_csrf_token_cookie_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        routes.login_callback()

        self.mock_redirect.return_value.set_cookie.assert_called_once_with('csrf_token', self.session['csrf_token'])

    def test_opts_in_to_session_expiration(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        routes.login()

        self.assertFalse(self.session.permanent)

    def test_redirects_to_ui_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}

        response = routes.login_callback()

        self.assertIs(self.mock_redirect.return_value, response)
        self.mock_redirect.assert_called_once_with('test-url-for-ui')

    def test_rejects_when_call_to_geoaxis_fails(self):
        self.mock_authenticate.side_effect = geoaxis.Unreachable()
        self.request.args = {'code': 'test-auth-code'}

        response = routes.login_callback()

        self.assertEqual(('Cannot log in: GeoAxis is unreachable', 500), response)

    def test_rejects_when_users_service_throws(self):
        self.mock_authenticate.side_effect = users.Error('oh noes')
        self.request.args = {'code': 'test-auth-code'}

        response = routes.login_callback()

        self.assertEqual(('Cannot log in: an internal error prevents authentication', 500), response)


class LogoutTest(helpers.MockableTestCase):
    def setUp(self):
        self.mock_url_for = self.create_mock('flask.url_for')
        self.mock_redirect = self.create_mock('flask.redirect')
        self.session = self.create_mock('flask.session')
        self.request = self.create_mock('flask.request')

    def test_clears_session(self):
        routes.logout()

        self.assertTrue(self.session.clear.called)


#
# Helpers
#

def create_user():
    return users.User(
        user_id='CN=test-commonname,O=test-org,C=test-country',
        api_key='test-api-key',
        name='test-name',
    )


class MockSession(dict):
    __setitem__ = dict.__setitem__
    __getitem__ = dict.__getitem__
