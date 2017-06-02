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
import re
import urllib.parse

import flask
import logging

from beachfront.services import users


PATTERN_VALID_RETURN_URL = re.compile(r'^https?://[^/]+\/')


def login():
    return_url = _get_return_url()
    if not return_url:
        return 'Cannot log in: invalid "return_url"', 400

    if flask.request.method == 'GET':
        return flask.render_template('login.jinja2')

    payload = flask.request.get_json()
    if not payload:
        payload = flask.request.form

    username = payload.get('username', '').strip()
    if not username:
        return flask.render_template('login.jinja2', error='missing username'), 401

    password = payload.get('password', '').strip()
    if not password:
        return flask.render_template('login.jinja2', error='missing password', username=username), 401

    try:
        user = users.authenticate_via_password(username, password)
    except users.Unauthorized:
        return flask.render_template('login.jinja2', error='invalid username or password', username=username), 401
    except users.Error:
        return flask.render_template('login.jinja2', error='an internal error prevents authentication', username=username), 500

    flask.session.permanent = False
    flask.session['api_key'] = user.api_key
    flask.session['csrf_token'] = os.urandom(32).hex()

    response = flask.redirect(return_url)
    response.set_cookie('csrf_token', flask.session['csrf_token'], domain=_get_cookie_domain())

    return response


def logout():
    log = logging.getLogger(__name__)

    if _is_logged_in():
        log.info('Logged out', actor=flask.request.user.user_id, action='log out')

    flask.session.clear()

    response = flask.redirect(_get_return_url() or '/')
    response.delete_cookie('csrf_token')

    return response


def _is_logged_in():
    return hasattr(flask.request, 'user')


def _get_cookie_domain():
    hostname = flask.request.host.split(':')[0]

    if hostname.count('.') < 2:
        return None  # Same domain

    return hostname.split('.', 1)[1]  # Parent domain


def _get_return_url() -> str:
    url = flask.request.args.get('return_url')
    if not url:
        return '/'

    candidate_hostname = urllib.parse.urlparse(url).hostname
    api_hostname = urllib.parse.urlparse(flask.request.host_url).hostname

    # Same domain
    if not candidate_hostname or candidate_hostname == api_hostname:
        return url

    api_parent_domain = api_hostname.split('.', 1)[-1]
    candidate_parent_domain = candidate_hostname.split('.', 1)[-1]

    # Sibling domains (e.g., a.example.com b.example.com)
    if api_parent_domain == candidate_parent_domain:
        return url

    # Reject everything else
    return None
