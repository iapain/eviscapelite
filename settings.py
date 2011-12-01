# Django settings for the example project.
import os
DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')
TEMPLATE_DEBUG = DEBUG
ROOT_URLCONF = 'urls'

import os
ROOT_PATH = os.path.dirname(__file__)
# Configuration settings for the session class.
session = {    
    "COOKIE_NAME": "eviscapelite_uuid",
    "DEFAULT_COOKIE_PATH": "/",
    "SESSION_EXPIRE_TIME": 12*7200,    # sessions are valid for 7200 seconds
                                    # (2 hours)
    "INTEGRATE_FLASH": False,        # integrate functionality from flash module?
    "SET_COOKIE_EXPIRES": True,     # Set to True to add expiration field to
                                    # cookie
    "WRITER":"datastore",           # Use the datastore writer by default. 
                                    # cookie is the other option.
    "CLEAN_CHECK_PERCENT": 50,      # By default, 50% of all requests will clean
                                    # the datastore of expired sessions
    "CHECK_IP": True,               # validate sessions by IP
    "CHECK_USER_AGENT": True,       # validate sessions by user agent
    "SESSION_TOKEN_TTL": 5,         # Number of seconds a session token is valid
                                    # for.
    "UPDATE_LAST_ACTIVITY": 60,     # Number of seconds that may pass before
                                    # last_activity is updated
}

# Configuration settings for the cache class
cache = {
    "DEFAULT_TIMEOUT": 3600, # cache expires after one hour (3600 sec)
    "CLEAN_CHECK_PERCENT": 50, # 50% of all requests will clean the database
    "MAX_HITS_TO_CLEAN": 20, # the maximum number of cache hits to clean
}

# Configuration settings for the flash class
flash = {
    "COOKIE_NAME": "appengine-utilities-flash",
}

# Configuration settings for the paginator class
paginator = {
    "DEFAULT_COUNT": 10,
    "CACHE": 10,
    "DEFAULT_SORT_ORDER": "ASC",
}

rotmodel = {
    "RETRY_ATTEMPTS": 3,
    "RETRY_INTERVAL": .2,
}

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".  Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(ROOT_PATH + '/templates'),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'middleware.sessionmiddleware.SessionMiddleware',
)


INSTALLED_APPS = (
    'app'
)