#!/usr/bin/env python

import os
import random
import string

import click
import passlib.hash

from beachfront import db


@click.group()
def cli():
    db.init()


@cli.command()
@click.argument('user_id')
@click.argument('full_name')
def add(user_id, full_name):
    user_id = user_id.lower()
    api_key = _create_api_key()
    password = _create_password()

    try:
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO useraccount (user_id, user_name, api_key, password_hash)
                VALUES (%(user_id)s, %(user_name)s, %(api_key)s, %(password_hash)s)
            """, {
                'user_id': user_id,
                'user_name': full_name,
                'api_key': api_key,
                'password_hash': passlib.hash.pbkdf2_sha256.hash(password),
            })
    except db.DatabaseError as err:
        _fail_immediately('user "{}" already exists'.format(user_id) if err.orig.pgcode == '23505' else str(err))

    click.secho('ADDED USER "{}"\n\n'
                '  password: {}\n'
                '   api key: {}\n'.format(user_id, password, api_key),
                fg='green')


@cli.command()
@click.argument('user-id')
def reset(user_id):
    user_id = user_id.lower()
    api_key = _create_api_key()
    password = _create_password()

    try:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE useraccount
                SET password_hash = %(password_hash)s,
                    api_key = %(api_key)s
                WHERE user_id = %(user_id)s
            """, {
                'user_id': user_id,
                'api_key': api_key,
                'password_hash': passlib.hash.pbkdf2_sha256.hash(password),
            })

            if not cursor.rowcount:
                _fail_immediately('USER "{}" NOT FOUND'.format(user_id))

    except db.DatabaseError as err:
        _fail_immediately(str(err))

    click.secho('RESET CREDENTIALS FOR USER "{}"\n\n'
                '  new password: {}\n'
                '   new api key: {}\n'.format(user_id, password, api_key),
                fg='green')


@cli.command(name='list')
def list_():
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT ROW_NUMBER() OVER (ORDER BY user_id) as n, user_id, user_name, created_on
                  FROM useraccount
                ORDER BY user_id
            """)

            if not cursor.rowcount:
                click.secho('NO USERS', fg='yellow')
                return

            click.secho('LIST USERS\n', fg='blue')
            for row in cursor.fetchall():
                click.secho('{:>5}  {:20}  {:40}  {}'.format(*row))

    except db.DatabaseError as err:
        _fail_immediately(str(err))


def _get_db_connection():
    try:
        return db.get_connection()
    except Exception as err:
        _fail_immediately('unknown error connecting to database: {}'.format(err))


def _create_api_key():
    return os.urandom(20).hex()


def _create_password():
    return ''.join(random.sample(string.ascii_letters, k=40))


def _fail_immediately(message):
    click.secho('ERROR: {}'.format(message), fg='red')
    exit(1)


if __name__ == '__main__':
    cli()
