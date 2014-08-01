from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('zobcs.views',
    # Examples:
    url(r'^/$', 'views_main'),
    url(r'^categories/$', 'views_categories'),
    url(r'^packages/(?P<category_id>\d+)/$', 'views_packages'),
    url(r'^ebuilds/(?P<package_id>\d+)/$', 'views_ebuilds'),
    url(r'^build/(?P<ebuild_id>\d+)/$', 'views_addbuild'),
    url(r'^buildinfo/(?P<ebuild_id>\d+)/(?P<buildlog_id>\d+)/$', 'views_buildinfo'),
    url(r'^showlog/(?P<log_id>\d+)/$', 'views_showlog'),
    url(r'^newpackages/$', 'views_newpackages'),
    url(r'^newlogs/$', 'views_newlogs'),
    url(r'^submitlog/(?P<buildlog_id>\d+)/$','views_buildinfo_bugzilla'),
)
urlpatterns+=patterns('',
    (r'^login/$', 'django.contrib.auth.views.login',{'template_name': 'pages/login.html'}),
    (r'^logout/$', 'django.contrib.auth.views.logout',{'template_name': 'pages/main.html'}),
    )