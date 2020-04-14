# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = (
    url(r'^$', views.tasks),
    url(r'^tasks/$', views.tasks),
    url(r'^record/$', views.record),
    url(r'^api/get_host/$', views.get_host),
    url(r'^api/execute/$', views.execute_script),
)
