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
from beachfront.routes import api_v0


def login_callback():
    query_params = flask.request.args

    auth_code = query_params.get('code', '').strip()
    if not auth_code:
        return 'Cannot log in: invalid "code" query parameter', 400

    try:
        user = users.authenticate_via_geoaxis(auth_code)
    except users.GeoAxisError as err:
        return 'Cannot log in: {}'.format(err), 500
    except users.Error:
        return 'Cannot log in: an internal error prevents authentication', 500

    flask.session.permanent = True
    flask.session['api_key'] = user.api_key
    flask.session['csrf_token'] = os.urandom(32).hex()

    response = flask.redirect(flask.url_for('ui'))
    response.set_cookie('csrf_token', flask.session['csrf_token'])

    return response


def login():
    return flask.render_template('login.jinja2',
                                 oauth_url=users.create_oauth_url())


def ui():
    if not _is_logged_in():
        return flask.redirect(flask.url_for('login'))

    return flask.render_template('ui.jinja2',
                                 user=flask.request.user)

def logout():
    log = logging.getLogger(__name__)

    if _is_logged_in():
        log.info('Logged out', actor=flask.request.user.user_id, action='log out')

    flask.session.clear()

    response = flask.redirect(flask.url_for('login'))
    response.delete_cookie('csrf_token')

    return response


def _is_logged_in():
    return hasattr(flask.request, 'user')
