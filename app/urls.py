from django.conf.urls.defaults import *

urlpatterns = patterns('app',
    # Example:
    (r'^dashboard', 'views.dashboard'),
    (r'^session/login', 'views.auth_request'),
    (r'^callback', 'views.auth_callback'),
    (r'^post', 'views.post'),
    (r'^comment/post/(?P<evi_id>\d+)', 'views.comment_post'),
    (r'^session/destroy', 'views.logout'),
    (r'^search', 'views.search'),
    (r'^$', 'views.home'),
    (r'^timeline/proxy/(?P<page>\d{1})', 'views.timeline_proxy'),
    (r'^comment/proxy/(?P<evi_id>\d+)', 'views.comment_proxy'),
    (r'^api/post', 'views.api_post'),
    (r'^api/timeline', 'views.api_timeline'),
)
