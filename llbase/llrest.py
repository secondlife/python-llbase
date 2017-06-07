#!/usr/bin/env python
###
### REST query library
###
## Copyright (c) 2015, Linden Research, Inc.
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.

import sys
import itertools
import json
import requests
from llbase import llsd
from xml.etree import cElementTree as ElementTree
from contextlib import contextmanager

class RESTError(Exception):
    """Describes an error from a RESTService request"""
    def __init__(self, service, url, status, msg):
        self.service = service
        self.url = url
        self.status = status
        self.msg = msg
        super(RESTError, self).__init__(msg)

class RESTEncodingBase(object):
    """Abstract base class for REST response types"""
    def __call__(self):
        # We don't (yet) have any stateful RESTEncoding classes. RESTService's
        # constructor calls its set_codec() method; set_codec() expects to be
        # passed a class, so it calls codec() to instantiate it. But
        # set_codec() returns the previous codec INSTANCE rather than just its
        # class. Providing a trivial base-class __call__() method allows us to
        # pass set_codec() (or RESTService's constructor) a codec instance.
        # This supports the possible future case of a stateful codec.
        return self
    def set_accept_header(self, session): # session is the requests.Session object
        raise NotImplementedError
    def decode(self, response): # response is the requests.response object
        """Given invalid input, this should raise ValueError"""
        raise NotImplementedError
    def set_content_type_header(self, session):
        # need not override this method if this codec needs no Content-Type header
        pass
    def encode(self, data):
        raise NotImplementedError

class RESTEncoding:
    """Classes that define the encoding/decoding for a RESTService"""
    class LLSD(RESTEncodingBase):
        def set_accept_header(self, session):
            # for most SL services, llsd is the default and we don't use a mime type to select it
            session.headers['Accept'] = '*/*'

        def decode(self, response):
            try:
                return llsd.parse(response.content)
            except llsd.LLSDParseError as err:
                raise ValueError("%s %s: failed to parse response as llsd: %s"
                             % (self.__class__.__name__, err.__class__.__name__, err))

        def set_content_type_header(self, session):
            session.headers['Content-Type'] = 'application/llsd'

        def encode(self, data):
            # If a particular REST API requires you to POST xml+llsd,
            # introduce an LLSDXML codec for the purpose... otherwise, use
            # notation.
            return llsd.format_notation(data)

    class JSON(RESTEncodingBase):
        def set_accept_header(self, session):
            session.headers['Accept'] = 'application/json'

        def decode(self, response):
            try:
                return response.json() # use decoding in requests
            except ValueError as err:
                raise ValueError("%s: failed to parse response as json: %s"
                                 % (self.__class__.__name__, err))

        def set_content_type_header(self, session):
            session.headers['Content-Type'] = 'application/json'

        def encode(self, data):
            return json.dumps(data)

    class XML(RESTEncodingBase):
        def set_accept_header(self, session):
            session.headers['Accept'] = 'application/xml'

        def decode(self, response):
            try:
                return ElementTree.fromstring(response.content)
            except Exception as err:
                raise ValueError("%s: %s parsing response as XML: %s"
                                 % (self.__class__.__name__, err.__class__.__name__, err))

        def set_content_type_header(self, session):
            session.headers['Content-Type'] = 'application/xml'

        def encode(self, data):
            return ElementTree.tostring(data)

    class HTML(RESTEncodingBase):
        def __init__(self):
            # Only import BeautifulSoup if explicitly instantiated.
            # Don't make llbase unconditionally depend on beautifulsoup4:
            # put that on the consumer who chooses this codec.
            global BeautifulSoup
            from bs4 import BeautifulSoup

        def set_accept_header(self, session):
            session.headers['Accept'] = 'text/html'

        def decode(self, response):
            try:
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as err:
                raise ValueError("%s: %s parsing response as HTML: %s"
                                 % (self.__class__.__name__, err.__class__.__name__, err))

        def set_content_type_header(self, session):
            # We have a no-op encode() method, so we'll pass caller's
            # structured data directly into requests function, which will
            # cause it to be form-encoded.
##          session.headers['Content-Type'] = 'x-www-form-urlencoded'
            # The above reasoning seems perfectly sound. However, when we use
            # this HTML codec to GET from TeamCity's REST API (which sometimes
            # emits HTML, as when retrieving a build artifact), passing the
            # above Content-Type header produces a 500 error! So... skip it.
            del session.headers["Content-Type"]

        def encode(self, data):
            return data

class RESTService(object):
    """
    Implements a simple wrapper for calling a REST interface that returns
    either llsd or json, with optional authentication.

    Any error in the HTTP request or parsing the response raises a RESTError,
    whose value describes the requested url and the error.

    Instantiate a RESTService for each service you need to use,
    and then use the get method on that service instance to execute requests.

    FooService = RESTService('Foo', 'https://foo.service.host/service/base/url', username='foouser', password='s3cr3t')
    try:
        result_data = FooService.get('query/path', params=dict(id='someid'))
    except RESTError as err:
        log.error("Error checking for someid : %s" % err)
        raise

    Parameters:
    name:            used in generating error messages
    baseurl:         a url prefix used for all requests to the service; may be an empty string
    codec:           one of the constants defined by the RESTEncoding class - determines expected request/response encoding
    authenticated:   a boolean: whether or not the service expects HTTP authentication (see get_credentials)
    username:        the username to be used for HTTP authentication
    password:        the password to be used for HTTP authentication
    proxy_hostport:  an HTTP proxy hostname and port number (host:port) through which requests should be routed
    
    Any other keyword parameters are passed through to the requests.Session() 
    """

    def __init__(self, name, baseurl, codec=RESTEncoding.LLSD, authenticated=True, username=None, password=None, proxy_hostport=None, **session_params):
        self.name = name
        self.baseurl = baseurl

        self.session = requests.Session(**session_params)
        self.codec = None               # set_codec() returns previous self.codec
        self.set_codec(codec)

        self.session.proxies = { 'http':'http://%s' % proxy_hostport, 'https':'http://%s' % proxy_hostport } \
          if proxy_hostport else None

        # defer setting the Session credentials to the request methods,
        # so that the _get_credentials method can provide prompting for them
        # when they are needed if get_credentials is not supplied as an override
        # or they are otherwise provided by the caller
        self.authenticated = authenticated
        self.username = username
        self.password = password

    def set_username(self, username):
        """Associate a username with the service; subsequent query calls to the service will use this"""
        self.authenticated = True
        self.username = username

    def set_password(self, password):
        """Associate a password with the service; subsequent query calls to the service will use this"""
        self.authenticated = True
        self.password = password

    def set_cert_authorities(self, capath):
        """Specify a path for certification verification; see http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification"""
        self.session.verify = capath

    def get_credentials(self):
        """
        This can be overridden by the service for obtaining credentials.
        It will be called at most once per service instance, and only if the service is authenticated
        and credentials have not been provided when the service is instantiated
        or using the set_ methods above.
        This default implementation gets the credentials from stdin, without echoing the password.
        """
        from getpass import getpass

        username = self.username if self.username else raw_input("\n%s username: " % self.name)
        password = self.password if self.password else getpass("%s password for '%s': " % (self.name, username))
        return ( username, password )

    def _get_credentials(self):
        """
        Provide the credentials in the form required by the 'requests' class,
        including returning (None,None) if the service is not authenticated.

        If credentials have not been set either at instantiation or using the set_ methods above,
        calls the get_credentials method to get them once and caches the results.
        """
        if self.authenticated:
            if not self.username or not self.password:
                (self.username, self.password) = self.get_credentials()
            return ( self.username, self.password )
        else:
            return None

    def _url(self,query):
        """Use whichever of self.baseurl and query isn't empty. If they're both present, join them with '/'"""
        return '/'.join(itertools.ifilter(None, (self.baseurl, query)))

    def get(self, query, params={}, **requests_params):
        """ Execute a GET request query against the service

            query:     request url path extension
                       if a baseurl was specified for the service, this is concatenated to it with '/'

            params:    dict of query param names with values.

            Any other keyword arguments are passed through to requests.get

            Returns the data as encoded by the response.

            Any error in the HTTP request or parsing the response raises a RESTError,
            whose value describes the requested url and the error.
        """
        # Execute the request and deal with any connection or server errors
        try:
            url=self._url(query)
            response = self.session.get(url, auth=self._get_credentials(), params=params)
            response.raise_for_status() # turns any error response into an exception

        except requests.exceptions.HTTPError as err:
            if response.status_code == 404:
                raise RESTError(self.name, response.request.url, response.status_code,
                                "%s: URL (%s) Not found" % (self.name, response.request.url))
            else:
                raise RESTError(self.name, response.request.url, response.status_code,
                                '%s: HTTP error: %s\n  for url: %s' % (self.name, err, response.request.url))
        except requests.exceptions.ConnectionError as err:
            raise RESTError(self.name, url, 499,
                            '%s: HTTP Connection error: %s\n  for url: %s' % (self.name, err, url))

        # Request returned success code, so decode the body per the service configuration
        try:
            return self.codec.decode(response)
        except ValueError as err:
            raise RESTError(self.name, response.request.url, response.status_code,
                            '%s: response error from url "%s":\n%s\nresponse data:\n%s'
                            % (self.name, response.request.url, err, response.text))

    def post(self, path, data, **requests_params):
        """
        Execute a POST against the service

        path:          url path extension
                       if a baseurl was specified for the service, this is
                       appended with '/'

        data:          the POST body
                       This can be structured data, according to what the
                       codec's encode() method expects. In particular, the XML
                       codec expects an xml.etree.Element.

        Any other keyword arguments are passed through to requests.post
        """
        url = self._url(path)

        try:
            encoded = self.codec.encode(data)
        except Exception as err:
            raise RESTError(self.name, url, '000',
                            '%s: %s encoding data: %s\n  for url: %s' %
                            (self.name, err.__class__.__name__, err, url))

        try:
            response = self.session.post(url, data=encoded, auth=self._get_credentials(), **requests_params)
            response.raise_for_status()

        except requests.RequestException as err:
            raise RESTError(self.name, response.request.url, response.status_code,
                            "%s: %s: %s\n  for url: %s" %
                            (self.name, err.__class__.__name__, err, url))

        # if the response body is non-empty, decode it
        if response.content:
            try:
                return self.codec.decode(response)
            except Exception as err:
                raise RESTError(self.name, response.request.url, response.status_code,
                                '%s: %s decoding response from url "%s":\n%s\nresponse data:\n%s'
                                % (self.name, err.__class__.__name__, response.request.url,
                                   err, response.text))

    def set_codec(self, codec):
        """
        Some services use different encodings for different operations. This
        method sets a new codec for all subsequent operations. It returns the
        previous codec.
        """
        old = self.codec
        # Our parameter could be a codec class, in which case we must
        # instantiate it. It could also be a RESTEncodingBase subclass
        # instance, but fortunately RESTEncodingBase.__call__() returns self,
        # so in that case the call below gets us the instance.
        self.codec = codec()
        self.codec.set_accept_header(self.session)
        self.codec.set_content_type_header(self.session)
        return old

    @contextmanager
    def temp_codec(self, codec):
        """
        Usage:

        with service.temp_codec(newcodec):
            service.get(...)

        temp_codec() sets newcodec for the duration of the 'with' body, then
        restores the previous codec when done.
        """
        prev = self.set_codec(codec)
        try:
            yield                       # execute 'with' body
        finally:
            self.set_codec(prev)

class SimpleRESTService(RESTService):
    """
    Subclass wrapper around RESTService to use the right defaults 
    for non-authenticated services
    """
    def __init__(self, name, baseurl, *args, **kwds):
        RESTService.__init__(self, name, baseurl, authenticated=False, *args, **kwds)
