# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import SelectScript, Doinfo
# Register your models here.


class Script(admin.ModelAdmin):
    list_display = ['scriptname', 'scriptcontent']
    search_fields = ['scriptname', 'scriptcontent']


class Info(admin.ModelAdmin):
    list_display = ['businessname', 'username', 'jobid', 'script', 'starttime', 'ipcount', 'status']
    search_fields = ['businessname', 'username', 'script', 'jobid']
    date_hierarchy = 'starttime'
    list_filter = ['businessname', 'username', 'script', 'jobid']


admin.site.register(SelectScript, Script)
admin.site.register(Doinfo, Info)