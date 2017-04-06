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
from datetime import datetime
from unittest.mock import patch

from test import helpers

from beachfront.db import DatabaseError
from beachfront.services import users
from beachfront.utils import geoaxis

API_KEY = '0123456789abcdef0123456789abcdef'


class AuthenticateViaGeoaxisTest(helpers.MockableTestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()

        self.logger = helpers.get_logger('beachfront.services.users')
        self.mock_insert_user = self.create_mock('beachfront.db.users.insert_user')
        self.mock_get_by_id = self.create_mock('beachfront.services.users.get_by_id')
        self.mock_oauth_client = self.create_mock('beachfront.services.users._oauth_client', autospec=True)

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

    def test_requests_token_from_geoaxis(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()

        users.authenticate_via_geoaxis('test-auth-code')

        self.mock_oauth_client.request_token.assert_called_once_with('test-geoaxis-redirect-uri', 'test-auth-code')

    def test_requests_profile_from_geoaxis(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()

        users.authenticate_via_geoaxis('test-auth-code')

        self.mock_oauth_client.request_token.assert_called_once_with('test-geoaxis-redirect-uri', 'test-auth-code')

    def test_creates_new_user_if_not_already_in_database(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertTrue(self.mock_insert_user.called)

    def test_does_not_create_new_user_if_already_in_database(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = users.User(user_id='test-uid', name='test-name')
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertFalse(self.mock_insert_user.called)

    def test_assigns_correct_api_key_to_new_users(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value.hex = 'lorem ipsum dolor'
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('lorem ipsum dolor', user.api_key)

    def test_assigns_correct_user_id_to_new_users(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-distinguished-name', user.user_id)

    def test_assigns_correct_name_to_new_users(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-commonname', user.name)

    def test_sends_correct_api_key_to_database(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value.hex = 'lorem ipsum dolor'
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('lorem ipsum dolor', self.mock_insert_user.call_args[1]['api_key'])

    def test_sends_correct_user_dn_to_database(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-distinguished-name', self.mock_insert_user.call_args[1]['user_id'])

    def test_sends_correct_user_name_to_database(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-commonname', self.mock_insert_user.call_args[1]['user_name'])

    def test_returns_an_existing_user(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        existing_user = users.User(user_id='test-uid', name='test-name')
        self.mock_get_by_id.return_value = existing_user
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual(existing_user, user)

    def test_throws_when_geoaxis_throws_during_token_request(self):
        self.mock_oauth_client.request_token.side_effect = geoaxis.Error('oh noes')
        with self.assertRaises(geoaxis.Error):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_throws_during_profile_request(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.side_effect = geoaxis.Error('oh noes')
        with self.assertRaises(geoaxis.Error):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_database_insertion_fails(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_logs_success_for_new_user(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - Users service auth geoaxis',
            'INFO - Creating user account for "test-distinguished-name"',
            'INFO - User "test-distinguished-name" has logged in successfully',
        ], self.logger.lines)

    def test_logs_success_for_existing_user(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = create_user()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - Users service auth geoaxis',
            'INFO - User "test-distinguished-name" has logged in successfully',
        ], self.logger.lines)

    def test_logs_failure_from_database_insert(self):
        self.mock_oauth_client.request_token.return_value = 'test-access-token'
        self.mock_oauth_client.get_profile.return_value = create_geoaxis_profile()
        self.mock_get_by_id.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - Users service auth geoaxis',
            'INFO - Creating user account for "test-distinguished-name"',
            'ERROR - Could not save user account "test-distinguished-name" to database',
        ], self.logger.lines)


class AuthenticateViaApiKeyTest(helpers.MockableTestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()

        self.logger = helpers.get_logger('beachfront.services.users')
        self.mock_select_user_by_api_key = self.create_mock('beachfront.db.users.select_user_by_api_key')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

    def test_returns_a_user(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        user = users.authenticate_via_api_key(API_KEY)
        self.assertIsInstance(user, users.User)

    def test_assigns_correct_user_id(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual('test-user-id', new_user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual('test-user-name', new_user.name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual(API_KEY, new_user.api_key)

    def test_throws_when_database_query_fails(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key(API_KEY)

    def test_throws_when_api_key_is_unauthorized(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_api_key(API_KEY)

    def test_throws_when_api_key_is_malformed(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.MalformedAPIKey):
            users.authenticate_via_api_key('definitely not correctly formed')

    def test_logs_success(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            'INFO - Users service auth api key',
        ], self.logger.lines)

    def test_logs_failure_from_unauthorized_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            'INFO - Users service auth api key',
            'ERROR - Unauthorized API key "0123456789abcdef0123456789abcdef"'
        ], self.logger.lines)

    def test_logs_failure_from_malformed_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.MalformedAPIKey):
            users.authenticate_via_api_key('definitely not correctly formed')
        self.assertEqual([
            'INFO - Users service auth api key',
            'ERROR - Cannot verify malformed API key: "definitely not correctly formed"'
        ], self.logger.lines)

    def test_logs_failure_from_database_select(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            'INFO - Users service auth api key',
            """ERROR - Database query for API key "0123456789abcdef0123456789abcdef" failed""",
        ], self.logger.lines)


class CreateOAuthURLTest(helpers.MockableTestCase):
    def setUp(self):
        self.mock_oauth_client = self.create_mock('beachfront.services.users._oauth_client', autospec=True)

    def test_sends_correct_redirect_uri_to_geoaxis(self):
        self.mock_oauth_client.authorize.return_value = 'test-auth-url'

        users.create_oauth_url()

        self.mock_oauth_client.authorize.assert_called_once_with('test-geoaxis-redirect-uri')

    def test_returns_correct_url(self):
        self.mock_oauth_client.authorize.return_value = 'test-auth-url'

        auth_url = users.create_oauth_url()

        self.assertEqual('test-auth-url', auth_url)


class GetByIdTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()

        self.logger = helpers.get_logger('beachfront.services.users')
        self.mock_select_user = self.create_mock('beachfront.db.users.select_user')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_throws_when_database_query_fails(self):
        self.mock_select_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.get_by_id('test-user-id')

    def test_returns_nothing_if_record_not_found(self):
        self.mock_select_user.return_value.fetchone.return_value = None
        user = users.get_by_id('test-user-id')
        self.assertEqual(None, user)

    def test_returns_a_user(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertIsInstance(user, users.User)

    def test_assigns_correct_user_id(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual('test-user-id', user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual('test-user-name', user.name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual(API_KEY, user.api_key)

    def test_logs_database_failure_during_select(self):
        self.mock_select_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.get_by_id('test-user-id')
        self.assertEqual([
            'ERROR - Database query for user ID "test-user-id" failed',
        ], self.logger.lines)


#
# Helpers
#

def create_geoaxis_profile():
    return geoaxis.Profile({
        'DN': 'test-distinguished-name',
        'email': 'test-email',
        'firstname': 'test-firstname',
        'lastname': 'test-lastname',
        'username': 'test-username',
        'commonname': 'test-commonname',
    })


def create_user():
    return users.User(
        user_id='test-distinguished-name',
        name='test-name',
    )


def create_user_db_record(user_id: str = 'test-user-id', api_key: str = API_KEY):
    return {
        'user_id': user_id,
        'user_name': 'test-user-name',
        'api_key': api_key,
        'created_on': datetime.utcnow(),
    }
