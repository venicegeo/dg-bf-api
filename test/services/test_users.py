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

API_KEY = '0123456789abcdef0123456789abcdef'


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
