# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.


class SelectScript(models.Model):
    scriptname = models.CharField(max_length=50, verbose_name='脚本名称')
    scriptcontent = models.TextField(verbose_name='脚本内容')

    def __str__(self):
        return self.scriptname