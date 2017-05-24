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

import json

import requests
import requests_mock

from test import helpers

from beachfront.utils import geoaxis


class OAuth2ClientTest(helpers.MockableTestCase):
    def setUp(self):
        self.logger = helpers.get_logger('geoaxis_client')
        self.mock_http = requests_mock.Mocker()
        self.mock_http.start()
        self.addCleanup(self.mock_http.stop)

    def test_can_instantiate(self):
        geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')

    def test_creates_authorization_urls(self):
        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        auth_url = client.authorize('test-redirect-uri', 'test-state')

        self.assertEqual('test-scheme://test-host/ms_oauth/oauth2/endpoints/oauthservice/authorize?', auth_url[:73])
        self.assertSetEqual({
            'client_id=test-client-id',
            'redirect_uri=test-redirect-uri',
            'response_type=code',
            'state=test-state',
        }, set(auth_url[73:].split('&')))

    def test_calls_correct_url_for_token_request(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_TOKEN_ISSUED)

        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        client.request_token('test-redirect-uri', 'test-auth-code')

        self.assertEqual('test-scheme://test-host/ms_oauth/oauth2/endpoints/oauthservice/tokens',
                         self.mock_http.request_history[0].url)

    def test_returns_access_tokens(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_TOKEN_ISSUED)

        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        access_token = client.request_token('test-redirect-uri', 'test-auth-code')

        self.assertEqual('test-access-token', access_token)

    def test_calls_correct_url_for_profile_request(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_PROFILE)

        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        client.get_profile('test-access-token')

        self.assertEqual('test-scheme://test-host/ms_oauth/resources/userprofile/me',
                         self.mock_http.request_history[0].url)

    def test_sends_correct_payload_to_token_request(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_TOKEN_ISSUED)

        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        client.request_token('test-redirect-uri', 'test-auth-code')

        self.assertSetEqual({
            'redirect_uri=test-redirect-uri',
            'code=test-auth-code',
            'grant_type=authorization_code',
        }, set(self.mock_http.request_history[0].body.split('&')))

    def test_sends_correct_access_token_to_profile_request(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_PROFILE)

        client = geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')
        client.get_profile('test-access-token')

        self.assertEqual('Bearer test-access-token',
                         self.mock_http.request_history[0].headers.get('Authorization'))

    def test_throws_when_token_request_is_denied(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_TOKEN_DENIED, status_code=401)

        with self.assertRaises(geoaxis.Unauthorized):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key')\
                .request_token('test-redirect-uri', 'test-auth-code')

    def test_throws_when_token_request_returns_error(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text='oh noes', status_code=500)

        with self.assertRaises(geoaxis.Error):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .request_token('test-redirect-uri', 'test-auth-code')

    def test_throws_when_token_request_if_geoaxis_is_unreachable(self):
        self.create_mock('requests.post').side_effect = requests.ConnectionError()

        with self.assertRaises(geoaxis.Unreachable):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .request_token('test-redirect-uri', 'test-auth-code')

    def test_throws_when_profile_request_is_denied(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_PROFILE_UNAUTHORIZED, status_code=401)

        with self.assertRaises(geoaxis.Unauthorized):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

    def test_throws_when_profile_request_returns_error(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text='oh noes', status_code=500)

        with self.assertRaises(geoaxis.Error):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

    def test_throws_when_profile_request_if_geoaxis_is_unreachable(self):
        self.create_mock('requests.get').side_effect = requests.ConnectionError()

        with self.assertRaises(geoaxis.Unreachable):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

    def test_throws_when_profile_response_is_missing_distinguished_name(self):
        mangled_profile = json.loads(RESPONSE_PROFILE)
        del mangled_profile['DN']
        self.mock_http.get('/ms_oauth/resources/userprofile/me', json=mangled_profile)

        with self.assertRaisesRegex(geoaxis.InvalidResponse, "missing 'DN'"):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

    def test_throws_when_profile_response_is_missing_user_name(self):
        mangled_profile = json.loads(RESPONSE_PROFILE)
        del mangled_profile['commonname']
        self.mock_http.get('/ms_oauth/resources/userprofile/me', json=mangled_profile)

        with self.assertRaisesRegex(geoaxis.InvalidResponse, "missing 'commonname'"):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

    def test_logs_failure_when_geoaxis_denies_token_request(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_TOKEN_DENIED, status_code=401)

        with self.assertRaises(geoaxis.Unauthorized):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .request_token('test-redirect-uri', 'test-auth-code')

        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 401:',
            '---',
            '',
            'Response: {',
            '    "error": "invalid_grant",',
            '    "error_description": "Invalid Grant: grant has been revoked; grant_type=azc "',
            '}',
            '',
            '---',
        ], self.logger.lines)

    def test_logs_failure_when_geoaxis_denies_profile_request(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_PROFILE_UNAUTHORIZED, status_code=401)

        with self.assertRaises(geoaxis.Unauthorized):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 401:',
            '---',
            '',
            'Response: {',
            '    "message": "Failed in authorization",',
            '    "oicErrorCode": "IDAAS-12345"',
            '}',
            '',
            '---',
        ], self.logger.lines)

    def test_logs_failure_when_geoaxis_throws_during_token_request(self):
        self.mock_http.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text='oh noes', status_code=500)

        with self.assertRaises(geoaxis.Error):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .request_token('test-redirect-uri', 'test-auth-code')

        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 500:',
            '---',
            '',
            'Response: oh noes',
            '',
            '---',
        ], self.logger.lines)

    def test_logs_failure_when_geoaxis_throws_during_profile_request(self):
        self.mock_http.get('/ms_oauth/resources/userprofile/me', text='oh noes', status_code=500)

        with self.assertRaises(geoaxis.Error):
            geoaxis.OAuth2Client('test-scheme', 'test-host', 'test-client-id', 'test-secret-key') \
                .get_profile('test-access-token')

        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 500:',
            '---',
            '',
            'Response: oh noes',
            '',
            '---',
        ], self.logger.lines)


#
# Fixtures
#

RESPONSE_PROFILE = """{
    "uid": "test-uid",
    "mail": "test-mail@localhost",
    "username": "test-username",
    "DN": "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country",
    "email": "test-email@localhost",
    "ID": "test-id",
    "lastname": "test-lastname",
    "login": "test-uid",
    "commonname": "test-commonname",
    "firstname": "test-firstname",
    "personatypecode": "AAA",
    "uri": "/ms_oauth/resources/userprofile/me/test-uid"
}"""

RESPONSE_PROFILE_UNAUTHORIZED = """{
    "message": "Failed in authorization",
    "oicErrorCode": "IDAAS-12345"
}"""

RESPONSE_TOKEN_ISSUED = """{
    "expires_in": 9999,
    "token_type": "Bearer",
    "access_token": "test-access-token"
}"""

RESPONSE_TOKEN_DENIED = """{
    "error": "invalid_grant",
    "error_description": "Invalid Grant: grant has been revoked; grant_type=azc "
}"""
