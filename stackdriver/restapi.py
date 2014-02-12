"""
restapi - base for calling rest resources

Stackdriver Public API, Copyright Stackdriver 2014

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import requests
import copy
import types

import json

import logging
logger = logging.getLogger(__name__)

def _wrap_transport_decorator(transport_func, wrapper, userdata):
    def inner(*args, **kwargs):
        return wrapper(transport_func, userdata=userdata, func_args=args, func_kwargs=kwargs)

    return inner

def transport_func(func):
    """ Decorates each of the transport functions that can get wrapped by a transport_controller """
    func._is_transport_func = True
    return func

class RestApi(object):

    def __init__(self, entrypoint_uri, version=None, apikey=None, username=None, password=None, useragent=None, transport_controller=None, transport_userdata=None):
        """
        Base class for accessing REST services

        :param entrypoint_path: The http or https uri to the api
        :param version: version of the api we support
        :param apikey: the stackdriver apikey to use for authentication
        :param username: username for basic auth - this is here for completeness but for the stackdriver apis auth should be done using the apikey
        :param password: password for basic auth - this is here for completeness but for the stackdriver apis auth should be done using the apikey
        :param transport_controller: if defined run this function before each network call
        :param transport_userdata: data to send to the transport_controller
        """

        # always end with a slash
        entrypoint_uri = entrypoint_uri.strip()
        if entrypoint_uri[-1] != '/':
            entrypoint_uri += '/'

        self._entrypoint_uri = entrypoint_uri
        self._apikey = apikey
        self._username = username
        self._password = password
        self._version = version
        self._useragent = useragent

        if transport_controller:
            self._decorate_transport_funcs(transport_controller, transport_userdata)

    def _decorate_transport_funcs(self, controller, userdata):
        """ decorate all methods that have an attribute of _is_transport_func set to True
            skip any methods that start with an underscore (_)

            SEE @transport_func decorator
        """
        for method_name in dir(self):
            if method_name.startswith('_'):
                continue

            method = getattr(self, method_name, None)
            if isinstance(method, types.MethodType):
                setattr(self, method_name, _wrap_transport_decorator(method, controller, userdata))

    def _merge_headers(self, extra, is_post=False):
        headers = {}
        if extra is not None:
            headers = copy.copy(extra)

        if self._apikey:
            headers['x-stackdriver-apikey'] = self._apikey
        headers['x-stackdriver-version'] = self._version

        if is_post:
            headers['accept'] = 'application/json, text/plain, */*'
            headers['content-type'] = 'application/json'

        if self._useragent:
            headers['user-agent'] = self._useragent

        return headers

    def _gen_full_endpoint(self, endpoint_path):
        if endpoint_path.startswith('/'):
            endpoint_path = endpoint_path[1:]

        return '%s%s' % (self._entrypoint_uri, endpoint_path)

    @transport_func
    def get(self, endpoint, params=None, headers=None):
        headers = self._merge_headers(headers)
        uri = self._gen_full_endpoint(endpoint)

        logger.debug('GET %s', uri, extra={'params': params})
        r = requests.get(uri, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

    @transport_func
    def post(self, endpoint, data=None, headers=None):
        headers = self._merge_headers(headers, is_post=True)
        uri = self._gen_full_endpoint(endpoint)

        logger.debug('POST %s', uri, extra={'data': data})
        r = requests.post(uri, data=json.dumps(data), headers=headers)
        r.raise_for_status()
        return r.json()

    @transport_func
    def put(self, endpoint, data=None, headers=None):
        headers = self._merge_headers(headers, is_post=True)
        uri = self._gen_full_endpoint(endpoint)

        logger.debug('PUT %s', uri, extra={'data': data})
        r = requests.put(uri, data=json.dumps(data), headers=headers)
        r.raise_for_status()
        return r.json()

    @transport_func
    def delete(self, endpoint, headers=None):
        headers = self._merge_headers(headers, is_post=True)
        uri = self._gen_full_endpoint(endpoint)

        logger.debug('DELETE %s', uri)
        r = requests.delete(uri, headers=headers)
        r.raise_for_status()
        return r.json()

    @property
    def api_version(self):
        return self._version

    @property
    def entrypoint(self):
        return self._entrypoint_uri
