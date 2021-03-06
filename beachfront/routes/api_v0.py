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

from datetime import datetime
from json import JSONDecodeError

import dateutil.parser
import dateutil.tz
import flask

from beachfront.db import DatabaseError
from beachfront.services import (algorithms as _algorithms,
                                 geoserver as _geoserver,
                                 jobs as _jobs,
                                 productlines as _productlines,
                                 scenes as _scenes)


blueprint = flask.Blueprint('v0', __name__)


#
# Algorithms
#

@blueprint.route('/algorithm/<service_id>', methods=['GET'])
def get_algorithm(service_id: str):
    try:
        algorithm = _algorithms.get(service_id)
    except _algorithms.NotFound:
        return 'Algorithm not found', 404
    return flask.jsonify({
        'algorithm': algorithm.serialize(),
    })


@blueprint.route('/algorithm', methods=['GET'])
def list_algorithms():
    algorithms = _algorithms.list_all()
    return flask.jsonify({
        'algorithms': [a.serialize() for a in algorithms],
    })


#
# Jobs
#

@blueprint.route('/job', methods=['POST'])
def create_job():
    try:
        payload = flask.request.get_json()
        job_name = _get_string(payload, 'name', max_length=100)
        planet_api_key = _get_string(payload, 'planet_api_key', max_length=64)
        service_id = _get_string(payload, 'algorithm_id', max_length=64)
        scene_id = _get_string(payload, 'scene_id', max_length=64)
    except JSONDecodeError:
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        return 'Invalid input: {}'.format(err), 400

    try:
        record = _jobs.create(
            user_id=flask.request.user.user_id,
            service_id=service_id,
            scene_id=scene_id,
            job_name=job_name.strip(),
            planet_api_key=planet_api_key,
        )
    except _jobs.PreprocessingError as err:
        return 'Cannot execute: {}'.format(err), 500
    except DatabaseError:
        return 'A database error prevents job execution', 500
    return flask.jsonify({
        'job': record.serialize(),
    }), 201


@blueprint.route('/job/<job_id>.geojson', methods=['GET'])
def download_geojson(job_id: str):
    try:
        detections = _jobs.get_detections(job_id)
    except _jobs.NotFound:
        return 'Job not found', 404
    except _jobs.Error as err:
        return 'Cannot download: {}'.format(err), 500
    except DatabaseError:
        return 'A database error prevents detection download', 500
    return detections, 200, {
        'Content-Type': 'application/vnd.geo+json',
    }


@blueprint.route('/job/<job_id>', methods=['DELETE'])
def forget_job(job_id: str):
    try:
        _jobs.forget(flask.request.user.user_id, job_id)
    except _jobs.NotFound:
        return 'Job not found', 404
    return 'Forgot {}'.format(job_id), 200


@blueprint.route('/job', methods=['GET'])
def list_jobs():
    jobs = _jobs.get_all(flask.request.user.user_id)
    return flask.jsonify({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })


@blueprint.route('/job/by_productline/<productline_id>', methods=['GET'])
def list_jobs_for_productline(productline_id: str):
    try:
        since = dateutil.parser.parse(
            flask.request.args.get('since', '1970-01-01', type=str),
        ).replace(tzinfo=dateutil.tz.tzutc())  # type: datetime
    except ValueError:
        return 'Invalid input: `since` value cannot be parsed as a valid date', 400
    jobs = _jobs.get_by_productline(productline_id, since)
    return flask.jsonify({
        'productline_id': productline_id,
        'since': since.isoformat(),
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })


@blueprint.route('/job/by_scene/<scene_id>', methods=['GET'])
def list_jobs_for_scene(scene_id: str):
    jobs = _jobs.get_by_scene(scene_id)
    return flask.jsonify({
        'scene_id': scene_id,
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        }
    })


@blueprint.route('/job/<job_id>', methods=['GET'])
def get_job(job_id: str):
    try:
        record = _jobs.get(flask.request.user.user_id, job_id)
    except _jobs.NotFound:
        return 'Job not found', 404
    return flask.jsonify({
        'job': record.serialize(),
    })


#
# Product Lines
#

@blueprint.route('/productline', methods=['POST'])
def create_productline():
    try:
        payload = flask.request.get_json()
        algorithm_id = _get_string(payload, 'algorithm_id', max_length=100)
        category = _get_string(payload, 'category', nullable=True, max_length=64)
        min_x = _get_number(payload, 'min_x', min_value=-180, max_value=180)
        min_y = _get_number(payload, 'min_y', min_value=-90, max_value=90)
        max_x = _get_number(payload, 'max_x', min_value=-180, max_value=180)
        max_y = _get_number(payload, 'max_y', min_value=-90, max_value=90)
        max_cloud_cover = int(_get_number(payload, 'max_cloud_cover', min_value=0, max_value=100))
        name = _get_string(payload, 'name', max_length=100)
        spatial_filter_id = _get_string(payload, 'spatial_filter_id', nullable=True, max_length=64)
        start_on = _get_datetime(payload, 'start_on')
        stop_on = _get_datetime(payload, 'stop_on', nullable=True)
    except JSONDecodeError:
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        return 'Invalid input: {}'.format(err), 400

    try:
        productline = _productlines.create_productline(
            algorithm_id=algorithm_id,
            bbox=(min_x, min_y, max_x, max_y),
            category=category,
            max_cloud_cover=max_cloud_cover,
            name=name,
            spatial_filter_id=spatial_filter_id,
            start_on=start_on.date(),
            stop_on=stop_on.date() if stop_on else None,
            user_id=flask.request.user.user_id,
        )
    except _algorithms.NotFound as err:
        return 'Algorithm {} does not exist'.format(err.service_id), 500
    except DatabaseError:
        return 'A database error prevents product line creation', 500
    return flask.jsonify({
        'productline': productline.serialize(),
    }), 201


@blueprint.route('/productline', methods=['DELETE'])
def delete_productline(productline_id: str):
    user_id = flask.request.user.user_id
    try:
        _productlines.delete_productline(user_id, productline_id)
    except DatabaseError:
        return 'A database error prevents deletion of this product line', 404
    except _productlines.NotFound:
        return 'Product line not found', 404
    except PermissionError:
        return 'User `{}` does not have permission to delete this product line'.format(user_id), 403
    return 'Deleted product line {}'.format(productline_id), 200


@blueprint.route('/productline', methods=['GET'])
def list_productlines():
    productlines = _productlines.get_all()
    return flask.jsonify({
        'productlines': {
            'type': 'FeatureCollection',
            'features': [p.serialize() for p in productlines],
        },
    })


#
# Profile
#

@blueprint.route('/user', methods=['GET'])
def get_user_data():
    return flask.jsonify({
        'profile': {
            'username': flask.request.user.user_id,
            'api_key': flask.request.user.api_key,
            'joined_on': flask.request.user.created_on,
        },
        'services': {
            'catalog': _scenes.create_catalog_url(),
            'wms_server': flask.request.host_url + 'wms',
        },
    })


#
# Scenes
#

@blueprint.route('/scene/<scene_id>.TIF', methods=['GET'])
def forward_to_geotiff(scene_id: str):
    planet_api_key = flask.request.args.get('planet_api_key')
    if not planet_api_key:
        return 'Missing `planet_api_key` parameter', 400

    user = getattr(flask.request, 'user', None)
    user_id = user.user_id if user else None
    try:
        scene = _scenes.get(scene_id, planet_api_key)
        geotiff_url = _scenes.activate(scene, planet_api_key, user_id)
    except _scenes.NotFound:
        return 'Cannot download: Scene `{}` not found'.format(scene_id), 404
    except (_scenes.CatalogError,
            _scenes.MalformedSceneID) as err:
        return 'Cannot download: {}'.format(err), 500

    if geotiff_url:
        return flask.redirect(geotiff_url)

    return flask.render_template('download_scene.jinja2', scene_id=scene_id), 202


#
# Helpers
#

def _get_datetime(d: dict, key: str, *, nullable: bool = False) -> datetime:
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and not value:
        return None
    try:
        value = dateutil.parser.parse(value)
    except:
        raise ValidationError('`{}` must be a valid timestamp'.format(key))
    return value


def _get_number(d: dict, key: str, *, min_value: int = None, max_value: int = None):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if not isinstance(value, int) and not isinstance(value, float):
        raise ValidationError('`{}` must be a number'.format(key))
    if min_value is not None and value < min_value or max_value is not None and value > max_value:
        raise ValidationError('`{}` must be a number between {} and {}'.format(key, min_value, max_value))
    return value


def _get_string(d: dict, key: str, *, nullable: bool = False, min_length: int = 1, max_length: int = 256):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError('`{}` must be a string'.format(key))
    value = value.strip()
    if len(value) > max_length or len(value) < min_length:
        raise ValidationError('`{}` must be a string of {}–{} characters'.format(key, min_length, max_length))
    return value


#
# Errors
#

class ValidationError(Exception):
    pass
