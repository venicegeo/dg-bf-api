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
import xml.etree.ElementTree as et
from unittest.mock import patch

import requests_mock
from requests import ConnectionError

from beachfront.services import geoserver

XMLNS = {'sld': 'http://www.opengis.net/sld'}


@requests_mock.Mocker()
class InstallIfNeededTest(unittest.TestCase):
    def test_calls_correct_urls(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/workspaces/beachfront')
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres')
        m.get('/geoserver/rest/layers/all_detections')
        m.get('/geoserver/rest/styles/detections')

        geoserver.install_if_needed()

        self.assertEqual([
            'https://vcap-geoserver.test.localdomain/geoserver/rest/workspaces/beachfront',
            'https://vcap-geoserver.test.localdomain/geoserver/rest/workspaces/beachfront/datastores/postgres',
            'https://vcap-geoserver.test.localdomain/geoserver/rest/layers/all_detections',
            'https://vcap-geoserver.test.localdomain/geoserver/rest/styles/detections',
        ], [h.url for h in m.request_history])

    def test_sends_correct_credentials(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/workspaces/beachfront')
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres')
        m.get('/geoserver/rest/layers/all_detections')
        m.get('/geoserver/rest/styles/detections')

        geoserver.install_if_needed()

        self.assertEqual([
            'Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk',
            'Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk',
            'Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk',
            'Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk',
        ], [h.headers['Authorization'] for h in m.request_history])

    def test_installs_workspace_if_missing(self, m):
        m.get('/geoserver/rest/workspaces/beachfront', status_code=404)
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres')
        m.get('/geoserver/rest/layers/all_detections')
        m.get('/geoserver/rest/styles/detections')

        with patch('beachfront.services.geoserver.install_workspace') as stub:
            geoserver.install_if_needed()

            stub.assert_called_once_with()

    def test_installs_datastore_if_missing(self, m):
        m.get('/geoserver/rest/workspaces/beachfront')
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres', status_code=404)
        m.get('/geoserver/rest/layers/all_detections')
        m.get('/geoserver/rest/styles/detections')

        with patch('beachfront.services.geoserver.install_datastore') as stub:
            geoserver.install_if_needed()

            stub.assert_called_once_with()

    def test_installs_detections_layer_if_missing(self, m):
        m.get('/geoserver/rest/workspaces/beachfront')
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres')
        m.get('/geoserver/rest/layers/all_detections', status_code=404)
        m.get('/geoserver/rest/styles/detections')

        with patch('beachfront.services.geoserver.install_layer') as stub:
            geoserver.install_if_needed()
            stub.assert_called_once_with('all_detections')

    def test_installs_detections_style_if_missing(self, m):
        m.get('/geoserver/rest/workspaces/beachfront')
        m.get('/geoserver/rest/workspaces/beachfront/datastores/postgres')
        m.get('/geoserver/rest/layers/all_detections')
        m.get('/geoserver/rest/styles/detections', status_code=404)

        with patch('beachfront.services.geoserver.install_style') as stub:
            geoserver.install_if_needed()
            stub.assert_called_once_with('detections')


@requests_mock.Mocker()
class InstallLayerTest(unittest.TestCase):
    def test_calls_correct_url(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/workspaces/beachfront/datastores/postgres/featuretypes', status_code=201)
        geoserver.install_layer('test-layer-id')
        self.assertEqual('https://vcap-geoserver.test.localdomain/geoserver/rest/workspaces/beachfront/datastores/postgres/featuretypes',
                         m.request_history[0].url)

    def test_sends_correct_credentials(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/workspaces/beachfront/datastores/postgres/featuretypes', status_code=201)
        geoserver.install_layer('test-layer-id')
        self.assertEqual('Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk', m.request_history[0].headers['Authorization'])

    def test_sends_correct_payload(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/workspaces/beachfront/datastores/postgres/featuretypes', status_code=201)

        geoserver.install_layer('test-layer-id')

        xml = et.fromstring(m.request_history[0].text)  # type: et.ElementTree
        self.assertEqual('test-layer-id', xml.findtext('./name'))
        self.assertEqual('-180.0', xml.findtext('./nativeBoundingBox/minx'))
        self.assertEqual('-90.0', xml.findtext('./nativeBoundingBox/miny'))
        self.assertEqual('180.0', xml.findtext('./nativeBoundingBox/maxx'))
        self.assertEqual('90.0', xml.findtext('./nativeBoundingBox/maxy'))
        self.assertEqual('test-layer-id', xml.findtext('./metadata/entry[@key="JDBC_VIRTUAL_TABLE"]/virtualTable/name'))
        self.assertIn('SELECT * FROM __beachfront__geoserver',
                      xml.findtext('./metadata/entry[@key="JDBC_VIRTUAL_TABLE"]/virtualTable/sql'))

    def test_throws_on_http_error(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/workspaces/beachfront/datastores/postgres/featuretypes', status_code=500)

        with self.assertRaises(geoserver.InstallError):
            geoserver.install_layer('test-layer-id')

    def test_throws_if_geoserver_is_unreachable(self, _):
        with patch('requests.post') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(geoserver.InstallError):
                geoserver.install_layer('test-layer-id')


@requests_mock.Mocker()
class InstallStyleTest(unittest.TestCase):
    def test_calls_correct_url_when_creating_sld(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        self.assertEqual('https://vcap-geoserver.test.localdomain/geoserver/rest/styles?name=test-style-id',
                         m.request_history[0].url)

    def test_calls_correct_url_when_setting_default_style(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        self.assertEqual('https://vcap-geoserver.test.localdomain/geoserver/rest/layers/all_detections',
                         m.request_history[1].url)

    def test_sends_correct_credentials_when_creating_sld(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        self.assertEqual('Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk', m.request_history[0].headers['Authorization'])

    def test_sends_correct_credentials_when_setting_default_style(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        self.assertEqual('Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk', m.request_history[1].headers['Authorization'])

    def test_sends_correct_payload_when_creating_sld(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        xml = et.fromstring(m.request_history[0].text)  # type: et.ElementTree
        self.assertEqual('#FF00FF', xml.findtext('.//sld:CssParameter', namespaces=XMLNS))

    def test_sends_correct_payload_when_setting_default_style(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections')
        geoserver.install_style('test-style-id')
        xml = et.fromstring(m.request_history[1].text)  # type: et.ElementTree
        self.assertEqual('detections', xml.findtext('defaultStyle/name'))

    def test_throws_on_http_error_when_creating_sld(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles', status_code=500)
        m.put('/geoserver/rest/layers/all_detections')
        with self.assertRaises(geoserver.InstallError):
            geoserver.install_style('test-style-id')

    def test_throws_on_http_error_when_setting_default_style(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        m.put('/geoserver/rest/layers/all_detections', status_code=500)
        with self.assertRaises(geoserver.InstallError):
            geoserver.install_style('test-style-id')

    def test_throws_if_geoserver_is_unreachable_when_creating_sld(self, _):
        with patch('requests.post') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(geoserver.InstallError):
                geoserver.install_style('test-style-id')

    def test_throws_if_geoserver_is_unreachable_when_setting_default_style(self, m: requests_mock.Mocker):
        m.post('/geoserver/rest/styles')
        with patch('requests.put') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(geoserver.InstallError):
                geoserver.install_style('test-style-id')


@requests_mock.Mocker()
class LayerExistsTest(unittest.TestCase):
    def test_calls_correct_url(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/layers/test-layer-id')
        geoserver.layer_exists('test-layer-id')
        self.assertEqual('https://vcap-geoserver.test.localdomain/geoserver/rest/layers/test-layer-id', m.request_history[0].url)

    def test_sends_correct_credentials(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/layers/test-layer-id')
        geoserver.layer_exists('test-layer-id')
        self.assertEqual('Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk', m.request_history[0].headers['Authorization'])

    def test_returns_false_if_not_exists(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/layers/test-layer-id', status_code=404)
        self.assertFalse(geoserver.layer_exists('test-layer-id'))

    def test_returns_true_if_exists(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/layers/test-layer-id')
        self.assertTrue(geoserver.layer_exists('test-layer-id'))

    def test_throws_if_geoserver_is_unreachable(self, _):
        with patch('requests.get') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(geoserver.InstallError):
                geoserver.layer_exists('test-layer-id')


@requests_mock.Mocker()
class StyleExistsTest(unittest.TestCase):
    def test_calls_correct_url(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/styles/test-style-id')
        geoserver.style_exists('test-style-id')
        self.assertEqual('https://vcap-geoserver.test.localdomain/geoserver/rest/styles/test-style-id', m.request_history[0].url)

    def test_sends_correct_credentials(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/styles/test-style-id')
        geoserver.style_exists('test-style-id')
        self.assertEqual('Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk', m.request_history[0].headers['Authorization'])

    def test_returns_false_if_not_exists(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/styles/test-style-id', status_code=404)
        self.assertFalse(geoserver.style_exists('test-style-id'))

    def test_returns_true_if_exists(self, m: requests_mock.Mocker):
        m.get('/geoserver/rest/styles/test-style-id')
        self.assertTrue(geoserver.style_exists('test-style-id'))

    def test_throws_if_geoserver_is_unreachable(self, _):
        with patch('requests.get') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(geoserver.InstallError):
                geoserver.style_exists('test-style-id')
