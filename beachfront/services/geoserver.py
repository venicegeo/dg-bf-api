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

import logging
import urllib.parse

import requests

from beachfront.config import GEOSERVER_HOST, GEOSERVER_SCHEME, GEOSERVER_USERNAME, GEOSERVER_PASSWORD, DATABASE_URI

WORKSPACE_ID = 'beachfront'
DATASTORE_ID = 'postgres'
DETECTIONS_LAYER_ID = 'all_detections'
DETECTIONS_STYLE_ID = 'detections'
TIMEOUT = 24


def create_wms_url():
    return '{}://{}/geoserver/wms'.format(GEOSERVER_SCHEME, GEOSERVER_HOST)


def get_wms_tile(params: dict):
    log = logging.getLogger(__name__ + '.geoserver_wms')

    url = '{}://{}/geoserver/wms'.format(GEOSERVER_SCHEME, GEOSERVER_HOST)

    log.info('Forwarding request to "%s"', url)
    try:
        response = requests.get(url, params, stream=True)
    except requests.ConnectionError as err:
        log.error('Connection to GeoServer failed: %s\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  '---',
                  err, err.request.url)
        raise Unreachable()

    if response.status_code != 200:
        log.error('GeoServer returned HTTP %s:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  '---',
                  response.status_code, response.request.url)
        raise Error('GeoServer returned HTTP {}'.format(response.status_code))

    return response.iter_content(chunk_size=8192), response.headers.get('Content-Type')


def install_if_needed():
    log = logging.getLogger(__name__)

    install_needed = False

    if not workspace_exists():
        install_needed = True
        install_workspace()

    if not datastore_exists():
        install_needed = True
        install_datastore()

    if not layer_exists(DETECTIONS_LAYER_ID):
        install_needed = True
        install_layer(DETECTIONS_LAYER_ID)

    if not style_exists(DETECTIONS_STYLE_ID):
        install_needed = True
        install_style(DETECTIONS_STYLE_ID)

    if install_needed:
        log.info('Installation complete!')
    else:
        log.info('GeoServer components exist and will not be reinstalled')


def install_datastore():
    log = logging.getLogger(__name__)

    log.info('Installing datastore `%s`', DATASTORE_ID, action='install datastore', actee='geoserver')

    database_uri = urllib.parse.urlparse(DATABASE_URI)
    try:
        response = requests.post(
            '{}://{}/geoserver/rest/workspaces/{}/datastores'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                WORKSPACE_ID,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/xml',
            },
            data="""
                <dataStore>
                    <name>{datastore_id}</name>
                    <type>PostGIS</type>
                    <connectionParameters>
                        <entry key="database">{database_name}</entry>
                        <entry key="host">{database_host}</entry>
                        <entry key="port">{database_port}</entry>
                        <entry key="passwd">{database_password}</entry>
                        <entry key="dbtype">postgis</entry>
                        <entry key="user">{database_username}</entry>
                    </connectionParameters>
                </dataStore>
            """.format(
                datastore_id=DATASTORE_ID,
                database_name=database_uri.path.strip('/'),
                database_host=database_uri.hostname,
                database_port=database_uri.port,
                database_username=database_uri.username,
                database_password=urllib.parse.unquote_plus(database_uri.password),
            )
        )
        log.debug('Sent request to geoserver:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  response.request.url,
                  response.request.body,
                  response.text)
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()

    if response.status_code != 201:
        log.error('Cannot create datastore `%s`:\n'
                  '---\n\n'
                  'HTTP %d\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  DATASTORE_ID,
                  response.status_code,
                  response.request.url,
                  response.request.body,
                  response.text)
        raise InstallError()


def install_workspace():
    log = logging.getLogger(__name__)

    log.info('Installing workspace `%s`', WORKSPACE_ID, action='install workspace', actee='geoserver')
    try:
        response = requests.post(
            '{}://{}/geoserver/rest/workspaces'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/xml',
            },
            data="""
                <workspace>
                    <name>{workspace_id}</name>
                </workspace>
            """.format(workspace_id=WORKSPACE_ID)
        )
        log.debug('Sent request to geoserver:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  response.request.url,
                  response.request.body,
                  response.text)
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()

    if response.status_code != 201:
        log.error('Cannot create workspace `%s`:\n'
                  '---\n\n'
                  'HTTP %d\n\n'
                  'URL: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  WORKSPACE_ID,
                  response.status_code,
                  response.request.url,
                  response.text)
        raise InstallError()


def install_layer(layer_id: str):
    log = logging.getLogger(__name__)

    log.info('Installing `%s`', layer_id, action='install layer', actee='geoserver')
    try:
        response = requests.post(
            '{}://{}/geoserver/rest/workspaces/{}/datastores/{}/featuretypes'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                WORKSPACE_ID,
                DATASTORE_ID,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/xml',
            },
            data=r"""
                <featureType>
                    <name>{layer_id}</name>
                    <title>All Detections</title>
                    <srs>EPSG:4326</srs>
                    <nativeBoundingBox>
                        <minx>-180.0</minx>
                        <maxx>180.0</maxx>
                        <miny>-90.0</miny>
                        <maxy>90.0</maxy>
                    </nativeBoundingBox>
                    <metadata>
                        <entry key="JDBC_VIRTUAL_TABLE">
                            <virtualTable>
                                <name>{layer_id}</name>
                                <sql>
                                    SELECT * FROM geoserver
                                     WHERE ('%jobid%' = '' AND '%productlineid%' = '' AND '%sceneid%' = '')
                                        OR (job_id = '%jobid%')
                                        OR (productline_id = '%productlineid%')
                                        OR (scene_id = '%sceneid%')
                                </sql>
                                <escapeSql>false</escapeSql>
                                <keyColumn>job_id</keyColumn>
                                <geometry>
                                    <name>geometry</name>
                                    <type>Geometry</type>
                                    <srid>4326</srid>
                                </geometry>
                                <parameter>
                                    <name>jobid</name>
                                    <regexpValidator>^(%|[a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}})$</regexpValidator>
                                </parameter>
                                <parameter>
                                    <name>productlineid</name>
                                    <regexpValidator>^[a-z]+$</regexpValidator>
                                </parameter>
                                <parameter>
                                    <name>sceneid</name>
                                    <regexpValidator>^\w+:\w+$</regexpValidator>
                                </parameter>
                            </virtualTable>
                        </entry>
                        <entry key="time">
                            <dimensionInfo>
                                <enabled>false</enabled>
                                <attribute>time_of_collect</attribute>
                                <presentation>CONTINUOUS_INTERVAL</presentation>
                                <units>ISO8601</units>
                                <defaultValue>
                                    <strategy>FIXED</strategy>
                                    <referenceValue>P1Y/PRESENT</referenceValue>
                                </defaultValue>
                            </dimensionInfo>
                        </entry>
                    </metadata>
                </featureType>
            """.strip().format(layer_id=layer_id),
        )
        log.debug('Sent request to geoserver:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  response.request.url,
                  response.request.body,
                  response.text)
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()

    if response.status_code != 201:
        log.error('Cannot create layer `%s`:\n'
                  '---\n\n'
                  'HTTP %d\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  layer_id,
                  response.status_code,
                  response.request.url,
                  response.request.body,
                  response.text)
        raise InstallError()


def install_style(style_id: str):
    log = logging.getLogger(__name__)
    log.info('Installing `%s`', style_id, action='install SLD', actee='geoserver')
    try:
        response = requests.post(
            '{}://{}/geoserver/rest/styles'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
            ),
            data="""
                <StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
                  <NamedLayer>
                    <UserStyle>
                      <FeatureTypeStyle>
                        <Rule>
                          <LineSymbolizer>
                            <Stroke>
                              <CssParameter name="stroke">#FF00FF</CssParameter>
                            </Stroke>
                          </LineSymbolizer>
                        </Rule>
                      </FeatureTypeStyle>
                    </UserStyle>
                  </NamedLayer>
                </StyledLayerDescriptor>
            """.strip(),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/vnd.ogc.sld+xml',
            },
            params={
                'name': style_id,
            },
        )
        log.debug('Sent request to geoserver:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  response.request.url,
                  response.request.body,
                  response.text)
        response.raise_for_status()
        response = requests.put(
            '{}://{}/geoserver/rest/layers/{}'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                DETECTIONS_LAYER_ID,
            ),
            data="""
                <layer>
                  <defaultStyle>
                    <name>{}</name>
                  </defaultStyle>
                </layer>
            """.strip().format(DETECTIONS_STYLE_ID),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/xml',
            },
        )
        response.raise_for_status()
        log.debug('Sent request to geoserver:\n'
                  '---\n\n'
                  'URL: %s\n\n'
                  'Request: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  response.request.url,
                  response.request.body,
                  response.text)
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()
    except requests.HTTPError as err:
        log.error('Cannot create style `%s`:\n'
                  '---\n\n'
                  'HTTP %d\n\n'
                  'URL: %s\n\n'
                  'Payload: %s\n\n'
                  'Response: %s\n\n'
                  '---',
                  style_id,
                  err.response.status_code,
                  err.response.request.url,
                  err.response.request.body,
                  err.response.text)
        raise InstallError()


def datastore_exists() -> bool:
    log = logging.getLogger(__name__)
    log.info('Checking for existence of datastore `%s`', DATASTORE_ID, action='check for datastore', actee='geoserver')
    try:
        response = requests.get(
            '{}://{}/geoserver/rest/workspaces/{}/datastores/{}'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                WORKSPACE_ID,
                DATASTORE_ID,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()
    return response.status_code == 200


def layer_exists(layer_id: str) -> bool:
    log = logging.getLogger(__name__)
    log.info('Checking for existence of layer `%s`', layer_id, action='check for layer', actee='geoserver')
    try:
        response = requests.get(
            '{}://{}/geoserver/rest/layers/{}'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                layer_id,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()
    return response.status_code == 200


def style_exists(style_id: str) -> bool:
    log = logging.getLogger(__name__)
    log.info('Checking for existence of style `%s`', style_id, action='check for style', actee='geoserver')
    try:
        response = requests.get(
            '{}://{}/geoserver/rest/styles/{}'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                style_id,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()
    return response.status_code == 200


def workspace_exists() -> bool:
    log = logging.getLogger(__name__)
    log.info('Checking for existence of workspace `%s`', WORKSPACE_ID, action='check for workspace', actee='geoserver')
    try:
        response = requests.get(
            '{}://{}/geoserver/rest/workspaces/{}'.format(
                GEOSERVER_SCHEME,
                GEOSERVER_HOST,
                WORKSPACE_ID,
            ),
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            timeout=TIMEOUT,
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise InstallError()
    return response.status_code == 200


#
# Errors
#


class Error(Exception):
    pass


class InstallError(Error):
    pass


class Unreachable(Error):
    pass
