import logging, os, sys

# Google App Engine imports.
from google.appengine.ext.webapp import util
from google.appengine.dist import use_library

# Remove the standard version of Django.
for k in [k for k in sys.modules if k.startswith('django')]:
  del sys.modules[k]



# Must set this env var *before* importing any part of Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

use_library('django', '1.1')

import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher
from django.core.signals import got_request_exception

def log_exception(*args, **kwds):
 logging.exception('Exception in request:')

# Log errors.
got_request_exception.connect(log_exception)

# Unregister the rollback event handler.
got_request_exception.disconnect(django.db._rollback_on_exception)


def main():
  # Create a Django application for WSGI.
  application = django.core.handlers.wsgi.WSGIHandler()

  # Run the WSGI CGI handler with that application.
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()