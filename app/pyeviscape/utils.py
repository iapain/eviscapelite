"""
Eviscape API wrapper
Author: Deepak Thukral<deepak@musicpictures.com>
PyEviscape provides functions for interacting with the Eviscape API.

The MIT License

Copyright (c) 2009 MMIX Musicpictures Ltd, Berlin
"""

import oauth
import urlparse
import re
from datetime import datetime, tzinfo, timedelta
from config import API_KEY, API_SECRET, FORMATTER
from xml.dom import minidom
from urllib import urlencode
from google.appengine.api import urlfetch

if FORMATTER == 'json':
    from django.utils import simplejson

API_VERSION = '1.0'
API_PROTOCOL = u'rest'
SERVER = 'www.eviscape.com'
API_URL = u'http://%s/api/%s/%s/' % (SERVER, API_VERSION, API_PROTOCOL)
API_DOCS = u'http://%s/api/%s/docs/' % (SERVER, API_VERSION)
API_RESPONSE_FORMAT = 'json' #this toolkit only support xml and json

signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()

REQUEST_TOKEN_URL = 'http://%s/oauth/request_token' % SERVER
ACCESS_TOKEN_URL = 'http://%s/oauth/access_token' % SERVER
AUTHORIZATION_URL = 'http://%s/oauth/authorize' % SERVER

CONSUMER_KEY = API_KEY
CONSUMER_SECRET = API_SECRET

CONSUMER = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)



class EviscapeError(Exception):
    pass

def request_oauth_resource(consumer, url, access_token, parameters=None, signature_method=signature_method, http_method='GET'):
    """
    usage: request_oauth_resource( consumer, '/url/', your_access_token, parameters=dict() )
    Returns a OAuthRequest object
    """
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer, token=access_token, http_url=url, parameters=parameters, http_method=http_method
    )
    oauth_request.sign_request(signature_method, consumer, access_token)
    return oauth_request


def fetch_response(oauth_request):
    url = oauth_request.to_url()
    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise EviscapeError
    return result.content

def fetch_urllib(oauth_request, params={}):
    url = oauth_request.to_url()
    if oauth_request.http_method.lower() == 'post':
        result = urlfetch.fetch(url=url,
                        payload=urlencode(params),
                        method=urlfetch.POST,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    else:
        result = urlfetch.fetch(url)
    
    if result.status_code != 200:
        raise EviscapeError, result.content
    return result.content

def get_unauthorised_request_token(callback=None, consumer=CONSUMER, signature_method=signature_method):
    "Ask Eviscape OAuth server for a request_token"
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer, oauth_callback=callback, http_url=REQUEST_TOKEN_URL
    )
    oauth_request.sign_request(signature_method, consumer, None)
    resp = fetch_response(oauth_request)
    token = oauth.OAuthToken.from_string(resp)
    return token


def get_authorisation_url(token, perms='write', consumer=CONSUMER, signature_method=signature_method):
    "Ask Eviscape OAuth server for a authroization URL"
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer, perms=perms, token=token, http_url=AUTHORIZATION_URL
    )
    oauth_request.sign_request(signature_method, consumer, token)
    return oauth_request.to_url()

def exchange_request_token_for_access_token(request_token, verifier, consumer=CONSUMER, signature_method=signature_method):
    "Exchange request token with access_token after authorization"
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer, token=request_token, oauth_callback=verifier, http_url=ACCESS_TOKEN_URL
    )
    oauth_request.sign_request(signature_method, consumer, request_token)
    resp = fetch_urllib(oauth_request)
    return oauth.OAuthToken.from_string(resp) 

def is_authenticated(access_token):
    "Checks if current access_token is good or not"
    oauth_request = request_oauth_resource(CONSUMER, API_URL,\
                                           access_token,\
                                           parameters={'method':'test.echo',\
                                                       'format':'json'})
    json = urlfetch.fetch(oauth_request.to_url()).content
    if 'auth_checked' in json:
        return True
    return False

class Bag(object):
    pass

#unmarshal taken and modified from pyamazon.py
#makes the xml easy to work with
def unmarshal(element):
    rc = Bag()
    if isinstance(element, minidom.Element):
        for key in element.attributes.keys():
            setattr(rc, key, element.attributes[key].value)
            
    childElements = [e for e in element.childNodes \
                     if isinstance(e, minidom.Element)]
    if childElements:
        for child in childElements:
            key = child.tagName
            if hasattr(rc, key):
                if type(getattr(rc, key)) <> type([]):
                    setattr(rc, key, [getattr(rc, key)])
                setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
            elif isinstance(child, minidom.Element) and \
                     (child.tagName == 'Details'):
                # make the first Details element a key
                setattr(rc,key,[unmarshal(child)])
                #dbg: because otherwise 'hasattr' only tests
                #dbg: on the second occurence: if there's a
                #dbg: single return to a query, it's not a
                #dbg: list. This module should always
                #dbg: return a list of Details objects.
            else:
                setattr(rc, key, unmarshal(child))
    else:
        #jec: we'll have the main part of the element stored in .text
        #jec: will break if tag <text> is also present
        text = "".join([e.data for e in element.childNodes \
                        if isinstance(e, minidom.Text)])
        setattr(rc, 'text', text)
    return rc

#unique items from a list from the cookbook
def uniq(alist):    # Fastest without order preserving
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

def prepare_params(params):
    """Convert lists to strings with ',' between items."""
    for (key, value) in params.items():
        if isinstance(value, list):
            params[key] = ','.join([item for item in value])
    return params

def get_data_xml(xml):
    """Given a bunch of XML back from Flickr, we turn it into a data structure
    we can deal with (after checking for errors)."""
    data = unmarshal(xml)
    if not data.rsp.stat == 'ok':
        msg = "ERROR [%s]: %s" % (data.rsp.err.code, data.rsp.err.msg)
        raise EviscapeError, msg
    return data

def get_data_json(json):
    if json['stat'] != 'ok':
        msg = "ERROR [%s]: %s" % (json['code'], json['msg'])
        raise EviscapeError, msg
    return json

def request_get(method, **params):
    params = prepare_params(params)
    url = '%s?method=%s&format=%s&nojsoncallback&%s' % (API_URL, method, FORMATTER, urlencode(params))
    if FORMATTER == 'json':
        return get_data_json(simplejson.loads(urlfetch.fetch(url).content))
    return get_data_xml(minidom.parseString(urlfetch.fetch(url).content))

def request_protected_get(method, access_token, **params):
    p = params
    p['method'] = method
    p['format'] = FORMATTER
    p['nojsoncallback'] = '1'
    params = prepare_params(params)
    url = '%s?method=%s&format=%s&nojsoncallback&%s' % (API_URL, method, FORMATTER, urlencode(params))
    oauth_request = request_oauth_resource(CONSUMER, url, access_token, parameters=p)
    a = oauth_request.to_url()
    if FORMATTER == 'json':
        return get_data_json(simplejson.loads(fetch_response(oauth_request)))
    return get_data_xml(minidom.parseString(fetch_response(oauth_request)))

def request_protected_post(method, access_token, **params):
    p = params
    p['method'] = method
    p['format'] = FORMATTER
    p['nojsoncallback'] = '1'
    params = prepare_params(params)
    url = '%s?method=%s&format=%s&nojsoncallback&%s' % (API_URL, method, FORMATTER, urlencode(params))
    oauth_request = request_oauth_resource(CONSUMER, url, access_token, parameters=p, http_method='POST')
    if FORMATTER == 'json':
        return get_data_json(simplejson.loads(fetch_urllib(oauth_request, params)))
    return get_data_xml(minidom.parseString(fetch_urllib(oauth_request, params)))


class Promise(object):
    pass

def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if isinstance(s, Promise):
        return unicode(s).encode(encoding, errors)
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s


class TZ(tzinfo):
    def utcoffset(self, dt): return timedelta(hours=2)

 
def parseDateTime(s):
    """Create datetime object representing date/time
       expressed in a string
    
    Takes a string in the format produced by calling str()
    on a python datetime object and returns a datetime
    instance that would produce that string.
    
    Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
                            "YYYY-MM-DD HH:MM:SS.ssssss",
                            "YYYY-MM-DD HH:MM:SS+HH:MM",
                            "YYYY-MM-DD HH:MM:SS"
    Where ssssss represents fractional seconds.	 The timezone
    is optional and may be either positive or negative
    hours/minutes east of UTC.
    """
    if s is None:
        return None
    # Split string in the form 2007-06-18 19:39:25.3300-07:00
    # into its constituent date/time, microseconds, and
    # timezone fields where microseconds and timezone are
    # optional.
    m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
                 str(s))
    datestr, fractional, tzname, tzhour, tzmin = m.groups()
    
    # Create tzinfo object representing the timezone
    # expressed in the input string.  The names we give
    # for the timezones are lame: they are just the offset
    # from UTC (as it appeared in the input string).  We
    # handle UTC specially since it is a very common case
    # and we know its name.
    
    # Convert the date/time field into a python datetime
    # object.
    x = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
    
    # Convert the fractional second portion into a count
    # of microseconds.
    if fractional is None:
        fractional = '0'
    fracpower = 6 - len(fractional)
    fractional = float(fractional) * (10 ** fracpower)
    
    # Return updated datetime object with microseconds and
    # timezone information.
    return x.replace(microsecond=int(fractional), tzinfo=TZ())
