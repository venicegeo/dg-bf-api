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

import flask
import logging

from beachfront.services import users


def login():
    username = flask.request.form.get('username', '').strip()
    if not username:
        return 'Cannot log in: missing username'

    password = flask.request.form.get('password', '').strip()
    if not password:
        return 'Cannot log in: missing password'

    try:
        user = users.authenticate_via_password(username, password)
    except users.Unauthorized:
        return 'Cannot log in: credentials rejected', 401
    except users.Error:
        return 'Cannot log in: an internal error prevents authentication', 500

    flask.session.permanent = False
    flask.session['api_key'] = user.api_key
    flask.session['csrf_token'] = os.urandom(32).hex()

    response = flask.make_response()
    response.set_cookie('csrf_token', flask.session['csrf_token'])

    return response


def logout():
    log = logging.getLogger(__name__)

    if _is_logged_in():
        log.info('Logged out', actor=flask.request.user.user_id, action='log out')

    flask.session.clear()

    response = flask.make_response()
    response.delete_cookie('csrf_token')

    return response


def _is_logged_in():
    return hasattr(flask.request, 'user')


def keepalive():
    return '', 204
