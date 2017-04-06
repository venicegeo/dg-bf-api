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

import os
import unittest

from beachfront import config
from beachfront.config._utils import _VCAPParser


class ConfigValueTest(unittest.TestCase):
    """
    This is probably more brittle than it needs to be, but this gives some
    small amount of protection against foot-shotgunning in prod.
    """

    def test_running_production_configuration(self):
        self.assertEqual('production', os.getenv('CONFIG'))

    def test_all_schemes_set_to_https(self):
        self.assertEqual('https', config.GEOSERVER_SCHEME)
        self.assertEqual('https', config.PIAZZA_SCHEME)
        self.assertEqual('https', config.CATALOG_SCHEME)
        self.assertEqual('https', config.GEOAXIS_SCHEME)


class VCAPParserTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self._VCAP_SERVICES = os.getenv('VCAP_SERVICES')

    def tearDown(self):
        os.environ['VCAP_SERVICES'] = self._VCAP_SERVICES

    def test_can_instantiate(self):
        _VCAPParser()

    def test_can_read_VCAP_SERVICES(self):
        os.environ['VCAP_SERVICES'] = """
            {
              "user-provided": [
                {
                  "name": "test-service-1",
                  "credentials": {
                    "database": "test-database",
                    "host": "test-host",
                    "hostname": "test-hostname",
                    "password": "test-password",
                    "port": "test-port",
                    "username": "test-username"
                  }
                },
                {
                  "name": "test-service-2",
                  "lorem": "ipsum",
                  "some": {
                    "arbitrarily": {
                      "nested": "value"
                    }
                  }
                }
              ],
              "random arbitrary top-level key": [
                {
                  "name": "test-service-3",
                  "credentials": {
                    "applesauce": "test-applesauce"
                  }
                }
              ]
            }
            """
        vcap = _VCAPParser()
        self.assertEqual({'test-service-1.name': 'test-service-1',
                          'test-service-1.credentials.database': 'test-database',
                          'test-service-1.credentials.host': 'test-host',
                          'test-service-1.credentials.hostname': 'test-hostname',
                          'test-service-1.credentials.username': 'test-username',
                          'test-service-1.credentials.password': 'test-password',
                          'test-service-1.credentials.port': 'test-port',
                          'test-service-2.name': 'test-service-2',
                          'test-service-2.lorem': 'ipsum',
                          'test-service-2.some.arbitrarily.nested': 'value',
                          'test-service-3.name': 'test-service-3',
                          'test-service-3.credentials.applesauce': 'test-applesauce',
                          }, vcap.SERVICES)

    def test_throws_when_VCAP_SERVICES_is_undefined(self):
        os.environ.pop('VCAP_SERVICES', None)

        with self.assertRaisesRegex(_VCAPParser.Error, 'VCAP_SERVICES cannot be blank'):
            _ = _VCAPParser().SERVICES

    def test_flags_error_if_VCAP_SERVICES_is_blank(self):
        os.environ['VCAP_SERVICES'] = ''

        with self.assertRaisesRegex(_VCAPParser.Error, 'VCAP_SERVICES cannot be blank'):
            _ = _VCAPParser().SERVICES

    def test_flags_error_if_VCAP_SERVICES_is_malformed(self):
        os.environ['VCAP_SERVICES'] = 'lolwut'

        with self.assertRaisesRegex(_VCAPParser.Error, 'in VCAP_SERVICES, JSONDecodeError'):
            _ = _VCAPParser().SERVICES

    def test_flags_error_if_service_name_is_missing(self):
        os.environ['VCAP_SERVICES'] = """
            {
              "user-provided": [
                {
                  "lorem": "ipsum"
                }
              ]
            }
            """

        with self.assertRaisesRegex(_VCAPParser.Error, 'VCAP_SERVICES, KeyError: \'name\''):
            _ = _VCAPParser().SERVICES
