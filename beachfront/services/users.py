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
import uuid
from datetime import datetime

import passlib.hash

from beachfront import db


TIMEOUT = 12
PATTERN_API_KEY = re.compile('^[a-f0-9]{32,}$')


class User:
    def __init__(
            self,
            *,
            user_id: str,
            name: str,
            api_key: str = None,
            created_on: datetime = None):
        self.user_id = user_id
        self.name = name
        self.api_key = api_key
        self.created_on = created_on

    def __str__(self):
        return self.user_id


def authenticate_via_api_key(api_key: str) -> User:
    log = logging.getLogger(__name__)
    log.info('Users service auth api key', action='service users auth api key')

    if not PATTERN_API_KEY.match(api_key):
        log.error('Cannot verify malformed API key: "%s"', api_key)
        raise MalformedAPIKey()

    log.debug('Checking "%s"', api_key)
    conn = db.get_connection()
    try:
        row = db.users.select_user_by_api_key(conn, api_key=api_key).fetchone()
    except db.DatabaseError as err:
        log.error('Database query for API key "%s" failed', api_key)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    if not row:
        log.error('Unauthorized API key "%s"', api_key)
        raise Unauthorized('CoastLine API key is not active')

    return User(
        user_id=row['user_id'],
        api_key=row['api_key'],
        name=row['user_name'],
        created_on=row['created_on'],
    )


def authenticate_via_password(user_id: str, plaintext_password: str) -> User:
    log = logging.getLogger(__name__)
    log.info('Users service auth geoaxis', action='service users auth geoaxis')

    with db.get_connection() as conn:
        password_hash = db.users.select_password_hash(conn, user_id=user_id)

    if not password_hash:
        raise Unauthorized('no such user')

    if not passlib.hash.pbkdf2_sha256.verify(plaintext_password, password_hash):
        raise Unauthorized('password mismatch')

    user = get_by_id(user_id)

    log.info('User "%s" has logged in successfully', user.user_id, actor=user.user_id, action='logged in')

    return user


def get_by_id(user_id: str) -> User:
    log = logging.getLogger(__name__)

    log.debug('Searching database for user "%s"', user_id)
    conn = db.get_connection()
    try:
        row = db.users.select_user(conn, user_id=user_id).fetchone()
    except db.DatabaseError as err:
        log.error('Database query for user ID "%s" failed', user_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    if not row:
        return None

    return User(
        user_id=row['user_id'],
        api_key=row['api_key'],
        name=row['user_name'],
        created_on=row['created_on'],
    )


def is_api_key(api_key):
    return PATTERN_API_KEY.match(api_key)


#
# Helpers
#

def _create_user(user_id, user_name) -> User:
    log = logging.getLogger(__name__)
    api_key = uuid.uuid4().hex

    log.info('Creating user account for "%s"', user_id, actor=user_id, action='create account')
    conn = db.get_connection()
    try:
        db.users.insert_user(
            conn,
            user_id=user_id,
            user_name=user_name,
            api_key=api_key,
        )
    except db.DatabaseError as err:
        log.error('Could not save user account "%s" to database', user_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    return User(
        user_id=user_id,
        name=user_name,
        api_key=api_key,
        created_on=datetime.utcnow(),
    )


#
# Errors
#

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MalformedAPIKey(Error):
    def __init__(self):
        super().__init__('Malformed API key')


class Unauthorized(Error):
    def __init__(self, message: str):
        super().__init__('Unauthorized: {}'.format(message))
