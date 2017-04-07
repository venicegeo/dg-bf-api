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

from .base import *


DOMAIN = 'int.geointservices.io'

ENFORCE_HTTPS = False

DATABASE_URI = 'postgres://beachfront:secret@localhost/beachfront'

SECRET_KEY = 'secret'

CATALOG_SCHEME = 'https'
CATALOG_HOST   = 'bf-ia-broker.int.geointservices.io'

PIAZZA_SCHEME  = 'https'
PIAZZA_HOST    = 'piazza.int.geointservices.io'

GEOAXIS_SCHEME       = 'http'
GEOAXIS_HOST         = 'localhost:5001'
GEOAXIS_CLIENT_ID    = 'beachfront'
GEOAXIS_SECRET       = 'lorem ipsum'
GEOAXIS_REDIRECT_URI = 'http://localhost:5000/login/callback'

GEOSERVER_SCHEME   = 'http'
GEOSERVER_HOST     = 'localhost:8080'
GEOSERVER_USERNAME = 'admin'
GEOSERVER_PASSWORD = 'geoserver'
