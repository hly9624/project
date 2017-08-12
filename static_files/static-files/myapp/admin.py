# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from django.contrib import admin
from myapp.models import *

# Register your models here.

class ArticleAdmin(admin.ModelAdmin):

    list_display = ('title', 'desc', 'click_count',)
    list_display_links = ('title', 'desc', )
    list_editable = ('click_count',)

    fieldsets = (
        (None, {
            'fields': ('title', 'desc', 'content', 'user', 'category', 'tag', )
        }),
        ('高级设置', {
            'classes': ('collapse',),
            'fields': ('click_count', 'is_recommend',)
        }),
    )

    class Media:
        js = (
            '/static/js/kindeditor-4.1.10/kindeditor-min.js',
            '/static/js/kindeditor-4.1.10/lang/zh_CN.js',
            '/static/js/kindeditor-4.1.10/config.js',
        )

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(User)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment)
admin.site.register(Links)
admin.site.register(Ad)
