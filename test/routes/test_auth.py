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

from test import helpers

from beachfront import routes
from beachfront.services import users


# class LogoutTest(helpers.MockableTestCase):
#     def setUp(self):
#         self.mock_url_for = self.create_mock('flask.url_for')
#         self.mock_redirect = self.create_mock('flask.redirect')
#         self.session = self.create_mock('flask.session')
#         self.request = self.create_mock('flask.request')
#
#     def test_clears_session(self):
#         routes.auth.logout()
#
#         self.assertTrue(self.session.clear.called)


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
