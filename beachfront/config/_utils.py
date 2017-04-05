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


class _LazyVCAPServicesParser:
    def __init__(self):
        self._services = None

    def __getitem__(self, item):
        if self._services is None:
            self._parse_services()
        return self._services[item]

    def _parse_services(self):
        def collect(node: dict):
            for k, v in node.items():
                path.append(k)
                if isinstance(v, dict):
                    collect(v)
                else:
                    services['.'.join(path)] = v
                path.pop()

        services = {}
        path = []

        vcap_services_ = os.getenv('VCAP_SERVICES')
        if not vcap_services_:
            raise _LazyVCAPServicesParser.Error('VCAP_SERVICES cannot be blank')

        try:
            vcap_dict = json.loads(vcap_services_)
            for key in vcap_dict.keys():
                for user_service in vcap_dict[key]:
                    path.append(user_service['name'])
                    collect(user_service)
                    path.pop()
        except TypeError as err:
            raise _LazyVCAPServicesParser.Error('encountered malformed entry: {}'.format(err))
        except KeyError as err:
            raise _LazyVCAPServicesParser.Error('some entry is missing property {}'.format(err))
        except json.JSONDecodeError as err:
            raise _LazyVCAPServicesParser.Error('invalid JSON: {}'.format(err))
        except Exception as err:
            raise _LazyVCAPServicesParser.Error(err)

        self._services = services

    class Error(Exception):
        def __init__(self, cause):
            super().__init__(': {}'.format(cause))


vcap_services = _LazyVCAPServicesParser()


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
                         'STATIC_URL_PATH'):
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
