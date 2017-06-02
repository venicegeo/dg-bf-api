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

import sys

import flask
import flask_cors

from beachfront import config, db, middleware, routes, services
from beachfront import DEBUG_MODE, MUTE_LOGS


def apply_middlewares(app: flask.Flask):
    app.before_request(middleware.https_filter)
    app.before_request(middleware.csrf_filter)
    app.before_request(middleware.auth_filter)
    app.after_request(middleware.apply_default_response_headers)


def attach_routes(app: flask.Flask):
    app.add_url_rule(methods=['POST', 'GET'], rule='/login/temporary_auth', view_func=routes.auth.login)
    app.add_url_rule(methods=['GET'], rule='/logout', view_func=routes.auth.logout)
    app.add_url_rule(methods=['GET'], rule='/wms', view_func=routes.wms.wms_proxy)

    app.register_blueprint(routes.api_v0.blueprint, url_prefix='/v0')

    @app.route('/favicon.ico')
    def favicon():
        return flask.redirect(flask.url_for('static', filename='favicon-dev.png'))

    @app.route('/')
    def health_check():
        return 'Hello'

    flask_cors.CORS(app, max_age=1200, supports_credentials=True)


def banner():
    configurations = []
    for key, value in sorted(config.__dict__.items()):
        if not key.isupper():
            continue
        configurations.append('{key:<20} : {value}'.format(key=key, value=value))

    warnings = []
    if DEBUG_MODE:
        warnings.append('  \u26A0  WARNING: SERVER IS RUNNING IN DEBUG MODE\n')

    if MUTE_LOGS:
        warnings.append('  \u26A0  WARNING: LOGS ARE MUTED\n')

    print(
        '-' * 120,
        '',
        *configurations,
        '',
        *warnings,
        '-' * 120,
        sep='\n',
        flush=True
    )


def init(app: flask.Flask):
    banner()
    db.init()

    app.secret_key = config.SECRET_KEY
    app.permanent_session_lifetime = config.SESSION_TTL
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    def static_url_for(path: str) -> str:
        return config.STATIC_BASEURL + path

    app.add_template_global(static_url_for)

    try:
        install_service_assets()
        apply_middlewares(app)
        attach_routes(app)
        start_background_tasks()
    except Exception as err:
        print(err)
        print('!' * 80, 'Initialization failed', err, '!' * 80, sep='\n\n', file=sys.stderr, flush=True)
        exit(4)  # Tell gunicorn not to infinitely respawn


def install_service_assets():
    services.geoserver.install_if_needed()


def start_background_tasks():
    services.jobs.start_worker()


################################################################################

#
# Bootstrapping
#

server = flask.Flask(__name__)
init(server)

################################################################################
