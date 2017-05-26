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
import re

import flask

from beachfront.config import ENFORCE_HTTPS
from beachfront.services import users

PATTERNS_PUBLIC_ENDPOINTS = (
    re.compile(r'^/$'),
    re.compile(r'^/favicon.ico$'),
    re.compile(r'^/login/temporary_auth$'),
    re.compile(r'^/v0/scene/[^/]+.TIF$'),
)

ENDPOINTS_DO_NOT_EXTEND_SESSION = ['/v0/job', '/v0/productline']


def apply_default_response_headers(response: flask.Response) -> flask.Response:
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Cache-Control', 'no-cache, no-store, must-revalidate, private')
    return response


def auth_filter():
    log = logging.getLogger(__name__)
    request = flask.request

    if request.method == 'OPTIONS':
        log.debug('Allowing preflight request to endpoint `%s`', request.path)
        return

    # Check session
    api_key = flask.session.get('api_key')

    # Check Authorization header
    if not api_key and request.authorization:
        api_key = request.authorization['username']

    if not api_key:
        if _is_public_endpoint(request.path):
            log.debug('Allowing access to public endpoint `%s`', request.path)
            return
        return 'Cannot authenticate request: API key is missing', 401

    try:
        log.debug('Attaching user to request context')
        request.user = users.authenticate_via_api_key(api_key)
    except users.Unauthorized as err:
        return str(err), 401
    except users.MalformedAPIKey:
        return 'Cannot authenticate request: API key is malformed', 401
    except users.Error:
        return 'Cannot authenticate request: an internal error prevents API key verification', 500


def csrf_filter():
    """
    Basic protection against Cross-Site Request Forgery in accordance with OWASP
    recommendations.

    Reference:
      https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
    """

    log = logging.getLogger(__name__)
    request = flask.request
    session = flask.session

    # Explicitly allow...

    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        log.debug('Allow: method is defined as "SAFE" by RFC2616')
        return

    if not session.get('api_key'):
        log.debug('Allow: no session exists')
        return

    csrf_token = session.get('csrf_token')
    if csrf_token and csrf_token == request.headers.get('X-XSRF-Token'):
        log.debug('Allow: CSRF token matches')
        return

    if request.authorization and users.is_api_key(request.authorization['username']):
        log.debug('Allow: API-key-based access')
        return

    # ...and reject everything else

    log.warning('Possible CSRF attempt:\n'
                '---\n\n'
                'Path: %s\n\n'
                'Origin: %s\n\n'
                'Referrer: %s\n\n'
                'IP: %s\n\n'
                'X-Requested-With: %s\n\n'
                'X-CSRF-Token: %s\n\n'
                '---',
                request.path,
                request.headers.get('Origin'),
                request.referrer,
                request.remote_addr,
                request.headers.get('X-Requested-With'),
                request.headers.get('X-XSRF-Token'),
                )
    return 'Access Denied: CSRF check failed', 403


def https_filter():
    log = logging.getLogger(__name__)
    request = flask.request

    if not ENFORCE_HTTPS:
        log.debug('HTTPS is not enforced')
        return

    if request.is_secure:
        log.debug('Allowing HTTPS request:\n'
                  '---\n\n'
                  'Path: %s\n'
                  'Referrer=`%s`', request.path, request.referrer)
        return

    log.warning('Rejecting non-HTTPS request: endpoint=`%s` referrer=`%s`',
                request.path,
                request.referrer)
    return 'Access Denied: Please retry with HTTPS', 403


#
# Helpers
#

def _is_public_endpoint(path: str) -> bool:
    for pattern in PATTERNS_PUBLIC_ENDPOINTS:
        if re.match(pattern, path):
            return True
    return False
