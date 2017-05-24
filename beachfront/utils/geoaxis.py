import logging
import urllib.parse

import requests


class OAuth2Client(object):
    def __init__(self, scheme, host, client_id, secret_key):
        self._client_id = client_id
        self._secret_key = secret_key
        self._auth_url = '{}://{}/ms_oauth/oauth2/endpoints/oauthservice/authorize'.format(scheme, host)
        self._token_url = '{}://{}/ms_oauth/oauth2/endpoints/oauthservice/tokens'.format(scheme, host)
        self._profile_url = '{}://{}/ms_oauth/resources/userprofile/me'.format(scheme, host)
        self._logger = logging.getLogger('geoaxis_client')

    def authorize(self, redirect_uri, state=''):
        """
        Builds URL to send user for authorization
        """
        return self._auth_url + '?' + urllib.parse.urlencode({
            'client_id':     self._client_id,
            'redirect_uri':  redirect_uri,
            'response_type': 'code',
            'state':         state,
        })

    def request_token(self, redirect_uri, auth_code):
        try:
            response = requests.post(
                self._token_url,
                auth=(self._client_id, self._secret_key),
                data={
                    'grant_type': 'authorization_code',
                    'code': auth_code,
                    'redirect_uri': redirect_uri,
                },
            )
            self._logger.debug('Requested OAuth access token from GeoAxis\n'
                               '---\n\n'
                               'Endpoint: %s\n\n'
                               'Auth Code: %s\n\n'
                               'Response: %s\n\n'
                               '---', response.request.url, auth_code, response.text)
        except requests.ConnectionError as err:
            self._logger.error('GeoAxis is unreachable: %s', err)
            raise Unreachable()

        if response.status_code != 200:
            self._logger.error('GeoAxis returned HTTP %s:\n'
                               '---\n\n'
                               'Response: %s\n\n'
                               '---', response.status_code, response.text)
            if response.status_code == 401:
                raise Unauthorized()
            raise Error('GeoAxis returned HTTP {}'.format(response.status_code))

        grant = response.json()

        token_type = grant.get('token_type')
        if not token_type:
            raise InvalidResponse("missing 'token_type' property", response.text)
        elif token_type != 'Bearer':
            raise InvalidResponse("unexpected value for 'token_type'", response.text)

        access_token = grant.get('access_token')
        if not access_token:
            raise InvalidResponse("missing 'access_token' property", response.text)

        return access_token

    def get_profile(self, access_token):
        try:
            response = requests.get(
                self._profile_url,
                headers={
                    'Authorization': 'Bearer {}'.format(access_token),
                },
            )
            self._logger.debug('Requested user profile from GeoAxis\n'
                               '---\n\n'
                               'Endpoint: %s\n\n'
                               'Access Token: %s\n\n'
                               'Response: %s\n\n'
                               '---', response.request.url, access_token, response.text)
        except requests.ConnectionError as err:
            self._logger.error('GeoAxis is unreachable: %s', err)
            raise Unreachable()

        if response.status_code != 200:
            self._logger.error('GeoAxis returned HTTP %s:\n'
                               '---\n\n'
                               'Response: %s\n\n'
                               '---', response.status_code, response.text)
            if response.status_code == 401:
                raise Unauthorized()
            raise Error('GeoAxis returned HTTP error {}'.format(response.status_code))

        try:
            return Profile(response.json())
        except KeyError as err:
            raise InvalidResponse('missing {} property'.format(err), response.text)


class Profile(object):
    def __init__(self, properties):
        self.distinguished_name = properties['DN']
        self.email = properties['email']
        self.first_name = properties['firstname']
        self.last_name = properties['lastname']
        self.username = properties['username']
        self.commonname = properties['commonname']


#
# Errors
#

class Error(Exception):
    pass


class InvalidResponse(Error):
    def __init__(self, details, response_text):
        Error.__init__(self, 'GeoAxis returned invalid response: {}'.format(details))
        self.response_text = response_text


class Unauthorized(Error):
    def __init__(self):
        Error.__init__(self, 'GeoAxis rejected code or client credentials')


class Unreachable(Error):
    def __init__(self):
        Error.__init__(self, 'GeoAxis is unreachable')
