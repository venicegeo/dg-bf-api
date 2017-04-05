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
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOMAIN = os.getenv('DOMAIN')

ENFORCE_HTTPS = True

SESSION_TTL = timedelta(minutes=30)

JOB_WORKER_INTERVAL = timedelta(seconds=60)
JOB_TTL             = timedelta(hours=2)

PIAZZA_SCHEME  = os.getenv('PIAZZA_SCHEME')
PIAZZA_HOST    = os.getenv('PIAZZA_HOST')
PIAZZA_API_KEY = os.getenv('PIAZZA_API_KEY')

STATIC_BASEURL = os.getenv('STATIC_BASEURL', '/static/')
