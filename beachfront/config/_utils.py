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
import os
import sys
import signal


class _VCAPParser:

    def __init__(self):
        self._cached_services = None

    @property
    def SERVICES(self) -> dict:
        if self._cached_services:
            return self._cached_services

        def _collect(node: dict):
            for k, v in node.items():
                path.append(k)
                if isinstance(v, dict):
                    _collect(v)
                else:
                    services['.'.join(path)] = v
                path.pop()

        services = {}
        path = []

        vcap_services = os.getenv('VCAP_SERVICES')
        if not vcap_services:
            raise self.Error('VCAP_SERVICES cannot be blank')

        try:
            vcap_dict = json.loads(vcap_services)
            for key in vcap_dict.keys():
                for user_service in vcap_dict[key]:
                    path.append(user_service['name'])
                    _collect(user_service)
                    path.pop()
        except Exception as err:
            raise self.Error('in VCAP_SERVICES, {}: {}'.format(err.__class__.__name__, err))

        self._cached_services = services

        return services

    class Error(Exception):
        pass


VCAP = _VCAPParser()


def validate(fatal: bool = True):
    from beachfront import config

    errors = []

    for required_key in ('DOMAIN',
                         'DATABASE_URI',
                         'GEOAXIS_SCHEME',
                         'GEOAXIS_HOST',
                         'GEOAXIS_CLIENT_ID',
                         'GEOAXIS_SECRET',
                         'GEOAXIS_REDIRECT_URI',
                         'GEOSERVER_SCHEME',
                         'GEOSERVER_HOST',
                         'GEOSERVER_USERNAME',
                         'GEOSERVER_PASSWORD',
                         'PIAZZA_HOST',
                         'PIAZZA_SCHEME',
                         'PIAZZA_API_KEY',
                         'SECRET_KEY',
                         'STATIC_BASEURL'):
        if not getattr(config, required_key, None):
            errors.append('{} cannot be blank'.format(required_key))

    if not errors:
        return

    error_message = 'Configuration error:\n{}'.format('\n'.join(['\t* ' + s for s in errors]))
    if fatal:
        print('!' * 80, error_message, '!' * 80, sep='\n\n', file=sys.stderr, flush=True)
        os.kill(os.getppid(), signal.SIGQUIT)
        signal.pause()
        exit(1)
    else:
        raise Exception(error_message)
