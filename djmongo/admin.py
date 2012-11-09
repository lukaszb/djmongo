"""
This module allows Django users to show djmongo.documents.Document within
admin site.

Example::

    from django.contrib import admin
    from djmongo.admin import DocumentAdmin
    from myapp.documents import Item


    class ItemAdmin(DocumentAdmin):
        document_list_display = ['title', 'url']

        def url(self, item):
            url = item.data.get('url', None)
            if not url:
                return '-'
            return '<a href="{url}">{url}</a>'.format(url=url)
        url.allow_tags = True

    admin.site.register(fix_document_for_admin(Item), SouthParkAdmin)



Admin support should be considered as work-in-progress.
"""
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re


DOCUMENT_PROXY_VAR_NAME = 'document_proxy'


def fix_document_for_admin(document):
    opts = document._meta
    opts.abstract = False
    opts.get_add_permission = lambda : 'add_%s' % opts.object_name.lower()
    opts.get_change_permission = lambda : 'change_%s' % opts.object_name.lower()
    opts.get_delete_permission = lambda : 'delete_%s' % opts.object_name.lower()
    return [document]


class DocumentChangeList(object):
    def __init__(self, request, model_admin, results):
        self.model_admin = model_admin
        self.document = model_admin.model
        self.opts = self.document._meta
        self.result_list = results
        self.result_count = self.full_result_count = len(results)
        self.date_hierarchy = None
        self.list_display = []
        self.formset = None
        self.page_num = int(request.GET.get('page', 0))

        self.multi_page = self.result_count > self.model_admin.list_per_page
        self.show_all = not self.multi_page
        self.can_show_all = self.show_all

        self.paginator = self.model_admin.get_paginator(request, results,
            self.model_admin.list_per_page)

        self.lookup_opts = {}

    def get_ordering_field_columns(self):
        return []

    def get_query_string(self, info):
        return '?page={p}'.format(**info)

    def get_results(self):
        return self.paginator.page(self.page_num + 1).object_list


class DocumentProxy(object):
    """
    Intermediate class for easier extraction of required data.
    """
    def __init__(self, document_admin):
        """
        :param document_admin: DocumentAdmin instance
        """
        self.document_admin = document_admin

    def get(self, item, key):
        """
        :param item: Document instance
        :param key: string
        """
        method = getattr(self.document_admin, key, None)
        if method:
            val = method(item)
            if getattr(method, 'allow_tags', False):
                val = mark_safe(val)
            else:
                val = escape(val)
            return val
        return item.data.get(key)


class DocumentAdmin(admin.ModelAdmin):
    fields = []
    document_list_display = ['_id']
    search_field = 'title'
    changelist_cls = DocumentChangeList

    def get_document_proxy(self):
        return DocumentProxy(self)

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):


        items = self.model.objects.all()
        query = request.GET.get('query')
        if self.search_field and query and re.match(r'[a-z \d]+', query, re.IGNORECASE):
            items = items.filter(**{'%s__icontains' % self.search_field: query})

        changelist = self.changelist_cls(request, self, items)

        data = {
            'items': changelist.get_results(),
            DOCUMENT_PROXY_VAR_NAME: self.get_document_proxy(),
            'is_popup': False,
            'opts': self.model._meta,
            'cl': changelist,
            'list_per_page': self.list_per_page,
            'list_display': self.document_list_display,
        }

        return render_to_response('admin/djmongo/changelist.html', data,
            RequestContext(request))

