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

from . import _utils
from .base import *


DATABASE_URI = 'postgres://{username}:{password}@{host}:{port}/{database}'.format(
    host=_utils.VCAP.SERVICES['pz-postgres.credentials.hostname'],
    port=_utils.VCAP.SERVICES['pz-postgres.credentials.port'],
    database=_utils.VCAP.SERVICES['pz-postgres.credentials.database'],
    username=_utils.VCAP.SERVICES['pz-postgres.credentials.username'],
    password=_utils.VCAP.SERVICES['pz-postgres.credentials.password'],
)

SECRET_KEY  = os.urandom(32).hex()

CATALOG_SCHEME = 'https'
CATALOG_HOST   = os.getenv('CATALOG_HOST')

PIAZZA_SCHEME  = 'https'
PIAZZA_HOST    = os.getenv('PIAZZA_HOST')
PIAZZA_API_KEY = os.getenv('PIAZZA_API_KEY')

GEOSERVER_SCHEME   = 'https'
GEOSERVER_HOST     = _utils.VCAP.SERVICES['pz-geoserver-efs.credentials.hostname']
GEOSERVER_USERNAME = _utils.VCAP.SERVICES['pz-geoserver-efs.credentials.username']
GEOSERVER_PASSWORD = _utils.VCAP.SERVICES['pz-geoserver-efs.credentials.password']
