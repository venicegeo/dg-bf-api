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
import requests
import uuid

from datetime import datetime
from bfapi import db

# TO-DO:
#   ** add in audit logging
#   ** add in unit tests
#   ** somehow test the thing
#   if receiving auth token directly from ui:
#       build rest endpoint to receive it that calls geoaxis_token_login and returns user_name + api_key
#   else
#       build function to call geoaxis with oauth auth code and derive auth token
#       as above, except endpoint receives auth code
#   plug the user from this in with the user from the user/jobs connection
#   probably worthwhile to invert db_harmonize.  In particular, the bits of user info associated with the
#       geoaxis return are effectively static.  The ones not associated with the geoaxis return could wind
#       up being *highly* dynamic.  Pulling that bit out of harmonize reduces by 1 the places where we might
#       shoot ourselves in the foot

class User:
    def __init__(
            self,
            *,
            geoaxis_uid: str,
            user_name: str,
            bf_api_key: str = None,
            created_on: datetime = None ): 
        self.geoaxis_uid = geoaxis_uid
        self.user_name = user_name
        self.bf_api_key = bf_api_key
        self.created_on = created_on

def geoaxis_token_login(geo_auth_token: str) -> User:
    try:
        response = requests.get(
            'https://{}/ms_oauth/resources/userprofile/me'.format(GEOAXIS_ADDR),
            timeout=TIMEOUT_LONG,
            headers={'Authorization': geo_auth_token},
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    uid = response.json().get('uid')
    if not uid:
        raise InvalidResponse('missing `uid`', response.text)
    user_name = response.json().get('username')
    if not user_name:
        raise InvalidResponse('missing `username`', response.text)
    
    geoax_user = User(
        geoaxis_uid = uid,
        user_name = user_name,
    )
    return _db_harmonize(inp_user=geoax_user)

def new_api_key(geoaxis_uid: str) -> str:
    updated_user = _db_harmonize(User(geoaxis_uid=geoaxis_uid, bf_api_key = uuid.uuid4()))
    return updated_user.bf_api_key

def login_by_api_key(bf_api_key: str) -> User:
    conn = db.get_connection()
    try:
        row = db.user.select_user_by_api_key(conn, api_key=bf_api_key).fetchone()
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        return None
    if row['api_key'] != bf_api_key:
        err = Exception("Database return error: select_user_by_api_key returned entry with incorrect api key.")
        db.print_diagnostics(err)
        raise err
    return User(
        geoaxis_uid=row['geoaxis_uid'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

def get_by_id(geoaxis_uid: str) -> User:
    conn = db.get_connection()
    try:
        row = db.user.select_user(conn, geoaxis_uid=geoaxis_uid).fetchone()
    except db.DatabaseError as err:
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    if not row:
        return None
    return User(
        geoaxis_uid=row['geoaxis_uid'],
        bf_api_key=row['api_key'],
        user_name=row['user_name'],
        created_on=row['created_on'],
    )

def _db_harmonize(inp_user: User) -> User:
    log = logging.getLogger(__name__)
    if inp_user is None:
        raise Exception("_db_harmonize called on empty User object")
    db_user = get_by_id(inp_user.geoaxis_uid)
    if db_user is None:
        if inp_user.bf_api_key == "":
            inp_user.bf_api_key = uuid.uuid4()
            
        conn = db.get_connection()
        transaction = conn.begin()
        try:
            db.user.insert_user(
                conn,
                geoaxis_uid=inp_user.geoaxis_uid,
                user_name=inp_user.user_name,
                api_key=inp_user.bf_api_key,
            )
            transaction.commit()
        except db.DatabaseError as err:
            transaction.rollback()
            log.error('Could not save user to database: %s', err)
            db.print_diagnostics(err)
            raise
        finally:
            conn.close()
        return inp_user
    else:
        if inp_user.user_name != "":
            db_user.user_name = inp_user.user_name
        if inp_user.bf_api_key != "":
            db_user.bf_api_key = inp_user.bf_api_key
        conn = db.get_connection()
        transaction = conn.begin()
        try:
            db.user.update_user(
                conn,
                geoaxis_uid=inp_user.geoaxis_uid,
                user_name=inp_user.user_name,
                api_key=inp_user.bf_api_key,
            )
            transaction.commit()
        except db.DatabaseError as err:
            transaction.rollback()
            log.error('Could not update user %s in database: %s', inp_user.geoaxis_uid, err)
            db.print_diagnostics(err)
            raise
        finally:
            conn.close()
        return db_user
