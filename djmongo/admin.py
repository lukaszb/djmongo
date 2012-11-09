from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
import re


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



class DocumentAdmin(admin.ModelAdmin):
    fields = []
    document_list_display = ['_id']
    search_field = 'title'
    changelist_cls = DocumentChangeList

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):


        items = self.model.objects.all()
        query = request.GET.get('query')
        if self.search_field and query and re.match(r'[a-z \d]+', query, re.IGNORECASE):
            items = items.filter(**{'%s__icontains' % self.search_field: query})

        changelist = self.changelist_cls(request, self, items)

        data = {
            'items': changelist.get_results(),
            'is_popup': False,
            'opts': self.model._meta,
            'cl': changelist,
            'list_per_page': self.list_per_page,
            'list_display': self.document_list_display,
        }

        return render_to_response('admin/djmongo/changelist.html', data,
            RequestContext(request))

