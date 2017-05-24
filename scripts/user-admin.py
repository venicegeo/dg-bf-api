#!/usr/bin/env python

import json
import os
import random
import string

import click
import passlib.hash
import psycopg2


@click.group()
def cli():
    pass


@cli.command()
@click.argument('user_id')
@click.argument('full_name')
def add(user_id, full_name):
    api_key = _create_api_key()
    password = _create_password()

    db = _connect_to_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO "user" (user_id, user_name, api_key, password_hash)
                VALUES (%(user_id)s, %(user_name)s, %(api_key)s, %(password_hash)s)
            """, {
                'user_id': user_id,
                'user_name': ' '.join(full_name),
                'api_key': api_key,
                'password_hash': passlib.hash.pbkdf2_sha256.hash(password),
            })
            db.commit()
    except psycopg2.Error as err:
        _fail_immediately('user "{}" already exists'.format(user_id) if err.pgcode == '23505' else str(err))

    click.secho('ADDED USER "{}"\n\n'
                '  password: {}\n'
                '   api key: {}\n'.format(user_id, password, api_key),
                fg='green')


@cli.command()
@click.argument('user-id')
def reset(user_id):
    api_key = _create_api_key()
    password = _create_password()

    db = _connect_to_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE "user"
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

            db.commit()
    except psycopg2.Error as err:
        _fail_immediately(str(err))

    click.secho('RESET CREDENTIALS FOR USER "{}"\n\n'
                '  new password: {}\n'
                '   new api key: {}\n'.format(user_id, password, api_key),
                fg='green')


@cli.command(name='list')
def list_():
    db = _connect_to_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT ROW_NUMBER() OVER (ORDER BY user_id) as n, user_id, user_name, created_on
                  FROM "public"."user"
                ORDER BY user_id
            """)

            if not cursor.rowcount:
                click.secho('NO USERS', fg='yellow')
                return

            click.secho('ALL USERS\n', fg='blue')
            for row in cursor.fetchall():
                click.secho('{:>5}  {:20}  {:40}  {}'.format(*row))

    except psycopg2.Error as err:
        _fail_immediately(str(err))


def _connect_to_db():
    try:
        credentials = None
        for service in sum(json.loads(os.environ['VCAP_SERVICES']).values(), []):
            if service['name'] == 'postgis':
                credentials = service['credentials']
                break
        if not credentials:
            _fail_immediately('database not found in VCAP_SERVICES')
        return psycopg2.connect(host=credentials['hostname'],
                                port=credentials['port'],
                                dbname=credentials['database'],
                                user=credentials['username'],
                                password=credentials['password'])
    except KeyError as err:
        _fail_immediately('VCAP_SERVICES parse error: {} {}'.format(err.__class__.__name__, err))
    except Exception as err:
        _fail_immediately('unknown error connecting to database: {}'.format(err))


def _create_api_key():
    return os.urandom(20).hex()


def _create_password():
    return ''.join(random.choices(string.ascii_letters, k=40))


def _fail_immediately(message):
    click.secho('ERROR: {}'.format(message), fg='red')
    exit(1)


if __name__ == '__main__':
    cli()
