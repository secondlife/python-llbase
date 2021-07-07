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

from contextlib import contextmanager
import itertools
import json
from llbase import llsd
import os
from pprint import pformat
import requests
import ssl
import sys
try:
    # python 3
    from urllib.parse import urlsplit, urlunsplit, SplitResult
    from http import cookiejar
except ImportError:
    # python 2
    from urlparse import urlsplit, urlunsplit, SplitResult
    import cookielib as cookiejar
from urllib3 import poolmanager
from xml.etree import cElementTree as ElementTree

try:
    unicode
except NameError:
    # In Python 3, str _is_ unicode; but for Python 2 it's still important to
    # distinguish.
    unicode = str

try:
    user_input = raw_input
except NameError:
    # Python 3
    user_input = input

class RESTError(Exception):
    """
    Describes an error from a RESTService request
    """
    def __init__(self, service, url, status, msg, **kwds):
        """
        Pass:

        service: the name of the RESTService instance generating the error
        url:     the URL in question
        status:  the HTTP status_code that failed
        msg:     the relevant error message
        kwds:    additional information to format into 'msg'

        'msg' will be prefixed with 'service:'.

        'msg' can be complete as passed, or it can contain format string
        references
        https://docs.python.org/2/library/string.html#format-string-syntax
        to {url} or {status} or any additional keyword argument passed to our
        constructor.
        """
        # When you first enter a function, locals() contains only its args.
        variables = locals().copy()
        # Allow caller to supplement name references with whatever s/he wants.
        variables.update(kwds)
        self.service = service
        self.url = url
        self.status = status
        # If 'msg' is passed as 8-bit str, but any of the 'variables' are
        # unicode, str.format() tries to encode them as 'ascii'. Ensure that
        # 'msg' is itself unicode before formatting.
        self.msg = ': '.join((service, unicode(msg).format(**variables)))
        super(RESTError, self).__init__(self.msg)

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
    @classmethod
    def name(cls):
        # Because we intentionally blur the distinction between passing a
        # RESTEncodingBase subclass and passing an *instance* of such a
        # subclass, for diagnostic purposes we want a method that will
        # reliably report the name of either. This is that method.
        return cls.__name__

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

class RESTEncoding(object):
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

    class LLSDXML(LLSD):

        """
            Some legacy applications that say they consume LLSD in their APIs actually consume
            LLSD+XML, so the LLSD codec above doesn't work.

            Almost all applications should be able to use the LLSD codec above,
            and this one shouldn't be used.
        """

        def set_accept_header(self, session):
            session.headers['Accept'] = 'application/llsd+xml'

        def set_content_type_header(self, session):
            session.headers['Content-Type'] = 'application/llsd+xml'

        def encode(self, data):
            return llsd.format_xml(data)

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

class _RESTService(object):
    """
    The _RESTService base class provides most of the implementation for
    RESTService. The RESTService subclass adds some parameter validation.

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

    To facilitate passing RESTService instances between unrelated modules,
    each operation supports an optional basepath= keyword argument. If you
    specify basepath='URL/path' instead of simply passing an operation-
    specific suffix to baseurl, the basepath you specify *replaces* the path
    part of the baseurl.

    A particular script might instantiate a RESTService that identifies the
    correct host, but appends 'httpAuth/app/rest' to the baseurl, since every
    operation in that script requires that prefix. The script might pass that
    RESTService to a function in a utility module that requires some
    completely different URL path: a path that does NOT start with
    'httpAuth/app/rest'. The utility function can pass its desired path as
    basepath rather than the normal path argument, which avoids introducing an
    undesired dependency between that module and the calling script.
    """

    # describe __init__() params; used by _resolve_args()
    init_params = ('name', 'baseurl', 'codec', 'authenticated',
                   'username', 'password', 'proxy_hostport', 'cert', 'basepath',
                   'cookie_policy')

    def __init__(self, name, baseurl, codec=RESTEncoding.LLSD, authenticated=True,
                 username=None, password=None, proxy_hostport=None, cert=None, basepath='',
                 cookie_policy=None, **session_params):
        """
        Parameters:
        name:            used in generating error messages
        baseurl:         a url prefix used for all requests to the service; may be an
                         empty string
        basepath:        a url path that overrides the path part of baseurl
        codec:           one of the constants defined by the RESTEncoding class -
                         determines expected request/response encoding
        authenticated:   a boolean: whether or not the service expects HTTP
                         authentication (see get_credentials)
        username:        the username to be used for HTTP authentication
        password:        the password to be used for HTTP authentication
        proxy_hostport:  an HTTP proxy hostname and port number (host:port)
                         through which requests should be routed
        cert:            string .pem pathname or (cert, key) pathname pair
                         https://2.python-requests.org/en/master/api/#requests.Session.cert
        cookie_policy:   http.cookiejar.CookiePolicy subclass for the session
                         https://docs.python.org/3/library/http.cookiejar.html#http.cookiejar.CookiePolicy
                         Special value cookie_policy=False blocks all cookies.

        Any other keyword parameters are passed through to the requests.Session() 
        """
        self.name = name
        self.baseurl = baseurl
        if basepath:
            # _url() returns a URL in which the path component of self.baseurl
            # is overridden by basepath. When basepath is passed to this
            # constructor, actually update self.baseurl with the result.
            self.baseurl = self._url(basepath, path='', method='__init__')

        self.session_params = session_params
        self.session = requests.Session(**session_params)
        self.codec = None               # set_codec() returns previous self.codec
        self.set_codec(codec)

        self.proxy_hostport = proxy_hostport
        self.session.proxies = { 'http': 'http://%s' % proxy_hostport,
                                 'https':'http://%s' % proxy_hostport } \
            if proxy_hostport else None
        if cert:
            self.session.cert = cert
        if cookie_policy is not None:
            if cookie_policy == False:
                # request implicit blocking
                cookie_policy = _BlockAllCookies()
            elif issubclass(cookie_policy, cookiejar.CookiePolicy):
                # set_policy() wants an instance, not a class
                cookie_policy = cookie_policy()
            self.session.cookies.set_policy(cookie_policy)

        # defer setting the Session credentials to the request methods,
        # so that the _get_credentials method can provide prompting for them
        # when they are needed if get_credentials is not supplied as an override
        # or they are otherwise provided by the caller
        self.authenticated = authenticated
        self.username = username
        self.password = password

    def clone(self, **kwds):
        """
        Return a RESTService instance configured the same as self, but with a
        different requests.Session instance for concurrent queries.

        Any constructor parameters can optionally be overridden for the new
        instance.
        """
        # Start with the relevant state from self
        newkwds = dict(name=self.name, baseurl=self.baseurl, codec=self.codec,
                       authenticated=self.authenticated,
                       username=self.username, password=self.password,
                       proxy_hostport=self.proxy_hostport,
                       cert=self.session.cert, **self.session_params)
        # then apply any overrides from parameters
        newkwds.update(kwds)
        # Allow for the possibility that we might actually be dealing with a
        # subclass -- which constrains subclasses to accept constructor params
        # just like our own.
        return self.__class__(**newkwds)

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

        username = self.username if self.username else user_input("\n%s username: " % self.name)
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

    def enable_old_tls(self):
        """
        As of 2020-09-10, Debian has disabled default support for TLS 1.0 and
        1.1. But sometimes we must contact one of our own older services. This
        workaround is from https://github.com/psf/requests/issues/4775.
        """
        self.session.mount('https://', _OldTLS())

    def _url(self, basepath, path, method, path_param='path', basepath_param='basepath'):
        """
        If basepath is None, the returned URL is (baseurl)/(path), allowing
        for the possibility that either might be empty.

        If basepath is valid, it overrides the path part of the baseurl. In
        other words, the returned URL is composed of:

        (baseurl scheme)://(baseurl host)/(basepath)/(path)

        The remaining parameters are to clarify the exception message if
        neither basepath nor path are passed.

        method is the name of our caller.

        path_param is the name of method's parameter passed to us as path.

        basepath_param is the name of method's parameter passed to us as basepath.
        """
        # if self.baseurl is None, use empty string instead
        baseurl = self.baseurl or ""
        if basepath:
            # Python 2's urlparse.urlunsplit(), unlike every other operation
            # that can mix str with unicode, complains if a SplitResult
            # contains both types. To avoid that, uniformly convert to unicode.
            
            # perhaps oddly, this split/unsplit dodge works even if baseurl is
            # the empty string
            baseurl = urlunsplit(urlsplit(unicode(baseurl))._replace(path=unicode(basepath)))

        # Use whichever of baseurl and path isn't empty. If they're both
        # present, join them with '/'
        return '/'.join(filter(None, (baseurl, path)))

    def get(self, query=None, params={}, basepath=None, **requests_params):
        """ Execute a GET request query against the service

            query:     request url path extension
                       if a baseurl was specified for the service, this is concatenated to it with '/'

            params:    dict of query param names with values.

            basepath:  replacement path part of baseurl

            Any other keyword arguments are passed through to requests.get

            Returns the data as encoded by the response.

            Any error in the HTTP request or parsing the response raises a RESTError,
            whose value describes the requested url and the error.
        """
        # Execute the request and deal with any connection or server errors
        url=self._url(basepath, query, method='get', path_param='query')
        with self._error_handling(url):
            response = self.session.get(url, auth=self._get_credentials(), params=params, **requests_params)
            response.raise_for_status() # turns any error response into an exception

        # Request returned success code, so decode the body per the service configuration
        return self._decode(response)

    def post(self, path=None, data={}, basepath=None, **requests_params):
        """
        Execute a POST against the service

        path:          url path extension
                       if a baseurl was specified for the service, this is
                       appended with '/'

        data:          the POST body
                       This can be structured data, according to what the
                       codec's encode() method expects. In particular, the XML
                       codec expects an xml.etree.Element.

        basepath:      replacement path part of baseurl

        Any other keyword arguments are passed through to requests.post
        """
        url = self._url(basepath, path, method='post')
        with self._error_handling(url):
            response = self.session.post(url, data=self._encode(url, data),
                                         auth=self._get_credentials(), **requests_params)
            response.raise_for_status()

        # decode the response body, if any
        return self._decode(response)

    def put(self, path=None, data={}, basepath=None, **requests_params):
        """
        Execute a PUT against the service

        path:          url path extension
                       if a baseurl was specified for the service, this is
                       appended with '/'

        data:          the PUT body
                       This can be structured data, according to what the
                       codec's encode() method expects. In particular, the XML
                       codec expects an xml.etree.Element.

        basepath:      replacement path part of baseurl

        Any other keyword arguments are passed through to requests.put
        """
        url = self._url(basepath, path, method='put')
        with self._error_handling(url):
            response = self.session.put(url, data=self._encode(url, data),
                                        auth=self._get_credentials(), **requests_params)
            response.raise_for_status()

        # decode the response body, if any
        return self._decode(response)

    def delete(self, path=None, basepath=None, **requests_params):
        """
        Execute a DELETE against the service

        path:          url path extension
                       if a baseurl was specified for the service, this is
                       appended with '/'

        basepath:      replacement path part of baseurl

        Any other keyword arguments are passed through to requests.delete
        """
        url = self._url(basepath, path, method='delete')
        with self._error_handling(url):
            response = self.session.delete(url, auth=self._get_credentials(),
                                           **requests_params)
            response.raise_for_status()

        # decode the response body, if any
        return self._decode(response)

    def _encode(self, url, data):
        try:
            return self.codec.encode(data)
        except Exception as err:
            raise RESTError(self.name, url, '000',
                            '{err.__class__.__name__} while {codec} encoding data: {err}\n'
                            '  for url: {url}', err=err, codec=self.codec.name())

    def _decode(self, response):
        # Don't bother passing an empty response body -- expected for most
        # operations -- to our codec.
        if not response.content:
            return ""

        try:
            return self.codec.decode(response)
        except Exception as err:
            text = response.text
            # Sometimes, as when we inadvertently reach a Google
            # authentication page, instead of (say) JSON we get a whole ton of
            # CSS + HTML. Building all that into the exception message doesn't
            # actually clarify the nature of the problem.
            limit = 512
            if len(text) > limit:
                text = text[:limit] + "..."
            raise RESTError(self.name, response.request.url, response.status_code,
                            '{err.__class__.__name__} while {codec} decoding response from url "{url}":\n'
                            '{err}\n'
                            'response data:\n'
                            '{text}', err=err, codec=self.codec.name(),
                            text=text)

    @contextmanager
    def _error_handling(self, url):
        """
        For internal use; unifies mapping requests.RequestException to RESTError.
        """
        try:
            with self._hide_http_proxy():
                # execute the body of the 'with' statement
                yield
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                self.RESTError_from_exc(url, err,
                                        "URL ({url}) Not found")
            else:
                self.RESTError_from_exc(url, err,
                                        'HTTP error: {err}\n'
                                        '  for url: {url}')
        except requests.exceptions.ConnectionError as err:
            # doubtful that ConnectionError produces any response content
            raise RESTError(self.name, url, 499,
                            'HTTP Connection error: {err}\n'
                            '  for url: {url}', err=err)
        except requests.RequestException as err:
            self.RESTError_from_exc(url, err,
                                    "{err.__class__.__name__}: {err}\n"
                                    "  for url: {url}")

    @staticmethod
    @contextmanager
    def _hide_http_proxy():
        """
        The requests library is sensitive to the presence of http_proxy in the
        environment. In fact, if http_proxy is visible to requests, any
        proxy_hostport passed to __init__() is IGNORED. This context manager
        temporarily hides http_proxy during the body of its 'with' statement.
        """
        # Remove http_proxy, if any, from this process's environment
        http_proxy = os.environ.pop('http_proxy', None)
        try:
            # execute body of 'with' statement
            yield
        finally:
            # restore http_proxy, if it was present to begin with
            if http_proxy is not None:
                os.environ['http_proxy'] = http_proxy

    def RESTError_from_exc(self, url, err, msg, **kwds):
        """
        Return a RESTError instance populated with self.name, the passed url
        and the status from the RequestException passed as err. Also, if there
        is a response and its body is non-empty, append the (decoded) response
        body to the message.
        """
        # First, make sure the exception is available for message formatting.
        kwds['err'] = err

        # Does this exception have a response attribute?
        try:
            response = err.response
        except AttributeError:
            # there's no response attached to the exception
            status = '000'

        else:
            # there is a response; doesn't necessarily imply a status_code
            status = getattr(response, 'status_code', '000')

            # only if there's a non-empty content attribute
            if getattr(response, 'content', None):
                # The response body may or may not be encoded as we expect. Try
                # decoding it -- but in this case, a decode failure isn't an error.
                try:
                    decoded = self.codec.decode(response)
                except Exception:
                    # We don't care why it failed -- means it's not encoded as we
                    # expected. The likely meaning is that the message is simply
                    # formatted for a human reader instead of as JSON or whatever. In
                    # any case, append non-empty response text.
                    _text = response.text
                else:
                    # Here we WERE able to decode the response, meaning it's probably
                    # structured Python data in some form. Use pformat() to aid
                    # human readability.
                    _text = pformat(decoded)

                # Either way, append {_text} to the original message, and add
                # _text to the available keywords. We do it this way instead
                # of simply appending _text to msg because pformat() will
                # produce curly braces, the content of which would be swallowed
                # by formatting internal to RESTError's constructor.
                msg = '\n'.join((msg, '{_text}'))
                kwds['_text'] = _text

        # Here we've either augmented msg and kwds, or we haven't. Either way,
        # deliver the RESTError we promised.
        raise RESTError(service=self.name, url=url, status=status, msg=msg, **kwds)

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

class RESTService(_RESTService):
    # We want the following validation for a consumer-instantiated
    # RESTService, just not for _RESTService instances implicitly constructed
    # by _resolve_args()
    def _url(self, basepath, path, method, path_param='path', basepath_param='basepath'):
        # Since caller accepts both 'basepath' and 'path', both are typically
        # optional arguments -- though 'path' is usually first so its caller
        # need not explicitly pass it as a keyword argument. But its caller
        # MUST pass one or the other.
        if not (basepath or path):
            # When you fail to pass a non-optional parameter, the interpreter
            # raises TypeError. Treat this similarly.
            raise TypeError("{}() requires either {} or {}"
                            .format(method, path_param, basepath_param))

        # we have one or the other, pass to base-class method
        return super(RESTService, self)._url(
            basepath=basepath, path=path, method=method,
            path_param=path_param, basepath_param=basepath_param)

class _OldTLS(requests.adapters.HTTPAdapter):
    """
    Helper for RESTService.enable_old_tls(), derived from
    https://github.com/psf/requests/issues/4775
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        # https://stackoverflow.com/a/59059052
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

class _BlockAllCookies(cookiejar.CookiePolicy):
    """
    Helper for RESTService(cookie_policy=False), derived from
    https://stackoverflow.com/a/21714597
    """
    netscape = True
    rfc2965 = False
    hide_cookie2 = False

    def return_ok(self, *args, **kwds):
        return False

    set_ok = return_ok
    domain_return_ok = return_ok
    path_return_ok = return_ok

class SimpleRESTService(RESTService):
    """
    Subclass wrapper around RESTService to use the right defaults 
    for non-authenticated services
    """
    def __init__(self, name, baseurl, *args, **kwds):
        RESTService.__init__(self, name, baseurl, authenticated=False, *args, **kwds)


# convenience functions for simple one-shot use cases
def get(url, **kwds):
    """
    url is the target URL; everything else must be keyword arguments

    RESTService.__init__() keywords are passed to RESTService constructor;
    the rest are passed to requests.get()
    """
    svc, kwds = _resolve_args('get', url, kwds)
    return svc.get(query='', basepath='', **kwds)

def post(url, **kwds):
    """
    url is the target URL; everything else must be keyword arguments

    RESTService.__init__() keywords are passed to RESTService constructor;
    data (if passed) is encoded according to the RESTService codec;
    the rest are passed to requests.post()
    """
    svc, kwds = _resolve_args('post', url, kwds)
    return svc.post(path='', basepath='', **kwds)

def put(url, **kwds):
    """
    url is the target URL; everything else must be keyword arguments

    RESTService.__init__() keywords are passed to RESTService constructor;
    data (if passed) is encoded according to the RESTService codec;
    the rest are passed to requests.put()
    """
    svc, kwds = _resolve_args('put', url, kwds)
    return svc.put(path='', basepath='', **kwds)

def delete(url, **kwds):
    """
    url is the target URL; everything else must be keyword arguments

    RESTService.__init__() keywords are passed to RESTService constructor;
    the rest are passed to requests.delete()
    """
    svc, kwds = _resolve_args('delete', url, kwds)
    return svc.delete(path='', basepath='', **kwds)

def _resolve_args(func, url, kwds):
    """
    Given a dict of **kwds, split them into _RESTService constructor params
    versus anything else, which we assume to be extra keywords to pass to
    'func'.

    Return (_RESTService instance, remaining kwds).
    """
    # _RESTService.init_params includes the first two parameters, name and
    # baseurl, to simplify maintenance. But since we pass those explicitly
    # here, remove from the set of keywords we recognize.
    init_params = set(_RESTService.init_params[2:])
    init_kwds = {}
    func_kwds = {}
    for key, value in kwds.items():
        if key in init_params:
            dest_kwds = init_kwds
        else:
            dest_kwds = func_kwds
        dest_kwds[key] = value
    return (_RESTService(name='temp ' + func, baseurl=url, **init_kwds),
            func_kwds)

    
