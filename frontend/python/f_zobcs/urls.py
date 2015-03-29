# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from django.conf.urls import patterns, include, url

urlpatterns = patterns('f_zobcs.views',
    url(r'^$', 'views_main'),
    url(r'^categories/$', 'views_categories'),
    url(r'^packages/(?P<category_id>\d+)/$', 'views_packages'),
    url(r'^ebuilds/(?P<package_id>\d+)/$', 'views_ebuilds'),
    url(r'^newbuild/(?P<ebuild_id>\d+)/(?P<config_id>\d+)/$', 'views_packagesbuildnew'),
    url(r'^buildinfo/(?P<ebuild_id>\d+)/(?P<buildlog_id>\d+)/$', 'views_buildinfo'),
    url(r'^showlog/(?P<log_id>\d+)/$', 'views_showlog'),
    url(r'^newpackages/$', 'views_newpackages'),
    url(r'^newlogs/$', 'views_newlogs'),
    url(r'^submitlog/(?P<buildlog_id>\d+)/$', 'views_buildinfo_bugzilla')
)
urlpatterns+=patterns('',
    (r'^login/$', 'django.contrib.auth.views.login',{'template_name': 'pages/login.html'}),
    (r'^logout/$', 'django.contrib.auth.views.logout',{'template_name': 'pages/main.html'}),
    )
