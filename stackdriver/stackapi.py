"""
stackapi - base for calling the Stackdriver API

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

from . import __version__

from .restapi import RestApi

import logging
logger = logging.getLogger(__name__)

class AnonStackInterface(object):
    def __init__(self, rest_class, client, endpoint_prefix=''):
        """
        This is returned by the StackApi attrs and provides a generic interface for calling
        REST actions on endpoints.  We use this so the client doesn't have to be updated
        every time a new object is added to the API.  This can also be extended for
        known objects in order to provide convenience functions for specific objects.
        """

        self._rest_class = rest_class
        self._rest_client = client

        # endpoint is always lowercase
        self._endpoint = '%s%s/' % (endpoint_prefix, self._rest_class.lower())

    def __call__(self, data=None):
        """ If called with data create an AnonStackObject """

        if data is None:
            data = {}

        if 'resource' in data:
            self._isrestclass(data['resource'], self._rest_class)

        return AnonStackObject(self._rest_class, self._rest_client, data)

    def __repr__(self):
        return '%s StackInterface (%s%s)' % (self._rest_class, self._rest_client.entrypoint, self._endpoint)

    def _wrap_rest_data_one(self, item):
        """ Wrap the returned item in an AnonStackObject """
        if 'resource' not in item:
            logger.warn('Trying to wrap an object without a resource, returning the raw dict instead.')
            return item

        # TODO: Lookup if there is a custom wrapper for this class
        cls = self._parse_class_from_resource(item['resource'])
        return AnonStackObject(cls, self._rest_client, item)

    def _wrap_rest_data(self, data):
        """
        Wrap the returned data in an AnonStackObject

        FIXME: This is a shallow wrapping right now but we should wrap anything that has a resource
        """
        if isinstance(data, dict):
            return self._wrap_rest_data_one(data)

        if not isinstance(data, list):
            raise RuntimeError("Result data must be a dict or a list: '%s' was returned" % type(data))

        objs = []
        for item in data:
            objs.append(self._wrap_rest_data_one(item))
        return objs

    def _parse_class_from_resource(self, resource):
        """
        parses the object type from the resource which is either in the form
        /<object>/<resource_id> or /<object>/<resource_id>/
        """
        parts = resource.split('/')
        if not parts[-1].rstrip():
            del parts[-1]

        cls = parts[-2]
        cls = cls[0].upper() + cls[1:].lower()
        return cls

    def _isrestclass(self, resource, cls):
        return self._parse_class_from_resource(resource) == cls

    def _unwind_result(self, result):
        """
        Unwinds the result set and returns the result data

        Result sets have a data and meta key.  The data contains the resources
        which were requested and the meta key contains extra information about
        the result set as a whole such as pagination data.

        Return the data

        TODO: If returning a list wrap data in a ResultSet class which
        has facilities for working with the metadata such as requesting
        the next page.
        """
        if 'data' not in result:
            logger.error('Result does not contain a data field')
            raise ValueError('Result does not contain a data field')

        return result['data']

    def _versioned_endpoint(self, endpoint, id=None, action=None):
        uri = 'v%s/%s' % (self._rest_client.api_version, endpoint)
        if id is not None:
            uri = '%s%s/' % (uri, id)
        if action is not None:
            uri = '%s%s/' % (uri, action)

        return uri

    def __getattr__(self, attr):
        """
        For any attr that starts with a capital letter and the rest are lowercase letters create a AnonStackInterface

        __getattr__ will only trigger if the attr is not defined on the class
        """
        if attr[0].isupper() and attr[1:].islower():
            # create an interface with the attr as the class for the endpoint
            return AnonStackInterface(attr, self._rest_client, self._endpoint)
        else:
            raise AttributeError

    def GET(self, id=None, params=None, action=None, headers=None):
        """ Call GET on the endpoint

            :param id: if this is specified tack on an id to the end of the URL for requesting a specific resource
            :param params: if a dictionary is sent in add the items as part of the URL's query string
            :param action: if specified call an action on a specified resource (adds the action at the end of the url)
        """
        endpoint = None
        endpoint = self._versioned_endpoint(self._endpoint, id, action)

        rest_result = self._rest_client.get(endpoint, params=params, headers=headers)

        return self._wrap_rest_data(self._unwind_result(rest_result))

    def POST(self, data=None, headers=None, action=None):
        """
        Call POST on the endpoint

        This is mainly for queries with json payloads.  For creation actions
        use the create method on the AnonStackObject class
        """
        endpoint = self._versioned_endpoint(self._endpoint, action=action)

        resp = self._rest_client.post(endpoint, data=data, headers=headers)

        result = self._unwind_result(resp)

        return result

    def LIST(self, params=None, headers=None):
        return self.GET(params=params, headers=headers)


class AnonStackObject(AnonStackInterface, dict):
    def __init__(self, rest_class, client, data):
        """
        Objects returned by the API are wrapped by this object

        This is an AnonStackInterface with added data that can be accessed like an attribute or a dict.
        For instance you can access the name field as such foo.name or foo['name'].  However if the data
        clashes with a defined function you need to use the dictionary access method.
        """
        if not isinstance(data, dict):
            raise TypeError('Object must be a dictionary')

        # copy all items in dict
        for key, value in data.iteritems():
            self[key] = value

        super(AnonStackObject, self).__init__(rest_class, client)

    def __getattr__(self, attr):
        if not attr in self:
            raise AttributeError

        return self[attr]

    def __setattr__(self, attr, value):
        if not attr.startswith('_'):
            self[attr] = value

        super(AnonStackObject, self).__setattr__(attr, value)

    def __repr__(self):
        return '%s(%s)' % (self._rest_class, dict.__repr__(self))

    def CREATE(self, headers=None):
        """ create an object record on the server """
        resource = self.get('resource', None)
        if resource:
            raise ValueError('Can not create, this resource already exists.')

        endpoint = self._versioned_endpoint(self._endpoint)
        resp = self._rest_client.post(endpoint, data=self, headers=headers)

        data = self._unwind_result(resp)

        # merge response in
        for key, value in data.iteritems():
            self[key] = value

        return self

    def _get_endpoint(self, action=None):
        endpoint = self.get('resource')
        if not endpoint:
            id = self.get('id')
            endpoint = self._versioned_endpoint(self._endpoint, id)

        if action is not None:
            endpoint = '%s%s/' % (endpoint, action)

        return endpoint

    def PUT(self, data=None, action=None, headers=None):
        endpoint = self._get_endpoint(action)
        resp = self._rest_client.put(endpoint, data=data, headers=headers)

        print resp
        result = self._unwind_result(resp)

        return result

    def GET(self, params=None, action=None, headers=None):
        endpoint = self._get_endpoint(action)
        resp = self._rest_client.get(endpoint, params=params, headers=headers)

        result = self._unwind_result(resp)

        return result

    def DELETE(self, headers=None):
        """ delete the object record on the server """
        resource = self.get('resource')
        if resource is None:
            raise ValueError('Can not delete, this is not a resource from the server.')

        resp = self._rest_client.delete(resource, headers=headers)

        data = self._unwind_result(resp)

        # merge response in
        for key, value in data.iteritems():
            self[key] = value

        return self


class StackApi(object):
    API_VERSION = '0.2'

    def __init__(self, entrypoint_uri='https://api.stackdriver.com/', version=API_VERSION, apikey=None, use_custom_headers=False, transport_controller=None, transport_userdata=None):
        """
        Entry point for the Stackdriver API

        :param entrypoint_uri: The url you wish to talk to
        :param version: The API version you wish to talk to
        :param apikey: The auth key used to talk to the API
            You can generate keys at https://app.stackdriver.com/settings/apikeys
            This must be set unless use_custom_headers or transport_controller is set
        :param use_custom_headers: If True the apikey does not have to be set and we assume
            you will be setting the key in the headers of each call
        :param transport_userdata: data sent to the transport_controller
        :param transport_controller: Advanced, if set all network calls will be decorated
            with this function. Use it to add advanced functionality such as key rotation
            and retries. A transport controller looks like this:

                from requests import HTTPError
                import sys

                def controller(transport_func, userdata=None, func_args=None, func_kwargs=None):
                    key_rotation = ['foo', 'bar', 'baz']
                    headers = func_kwargs.get('headers')
                    if not headers:
                        headers = {}

                    last_exception = None
                    for key in key_rotation:
                        try:
                            headers['x-stackdriver-apikey'] = key
                            func_kwargs['headers'] = headers
                            return transport_func(*func_args, **func_kwargs)

                        except HTTPError as e:
                            if e.response.status_code == 401: # Unauthorized
                                # we want to rotate the keys so do nothing (you can also log here)
                                last_exception = sys.exc_info()
                            else:
                                # reraise all other errors
                                raise

                     # If we get here reraise the last Unauthorized exception in the original context
                     raise last_exception[1], None, last_exception[2]
        """
        if not apikey and not use_custom_headers and not transport_controller:
            raise KeyError('apikey must be specified when talking to the Stackdriver API')

        # add the version template to the entrypoint
        entrypoint_uri = entrypoint_uri.strip()
        if entrypoint_uri[-1] != '/':
            entrypoint_uri += '/'

        self._rest_client = RestApi(entrypoint_uri,
                                    version,
                                    apikey,
                                    useragent='Stackdriver Python Client %s' % __version__,
                                    transport_controller=transport_controller,
                                    transport_userdata=transport_userdata)

    def __getattr__(self, attr):
        """
        For any attr that starts with a capital letter and the rest are lowercase letters create a AnonStackInterface

        __getattr__ will only trigger if the attr is not defined on the class
        """
        if attr[0].isupper() and attr[1:].islower():
            # create an interface with the attr as the class for the endpoint
            return AnonStackInterface(attr, self._rest_client)
        else:
            raise AttributeError
