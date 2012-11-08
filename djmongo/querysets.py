import pymongo
from django.utils.datastructures import SortedDict


class QuerySet(object):

    def __init__(self, document, filters=None, ordering=None):
        self.document = document
        self._filters = filters or {}
        self._ordering = ordering or []
        self.offset = None
        self.limit = None

    def __iter__(self):
        for item in self.get_items():
            yield self.document(data=item)

    def __getitem__(self, index):
        if isinstance(index, slice):
            queryset = self.clone()
            queryset.offset = index.start
            if index.stop:
                limit = index.stop
                if index.start:
                    limit -= index.start
                queryset.limit = limit
            return queryset
        if isinstance(index, int):
            return list(self.clone()[index:index+1])[0]
        raise TypeError("QuerySet index should be int or slice (is: %s)"
            % index.__class__)

    def get_filters(self):
        for key in (k for k in self._filters if '__' in k):
            field, operator = key.split('__', 1)
            if operator in ['in']:
                self._filters[field] = {'$' + operator: list(self._filters.pop(key))}
        return self._filters

    def get_ordering(self):
        ordering = SortedDict()
        for order in self._ordering:
            key = order
            val = pymongo.ASCENDING
            if order[0] == '-':
                key = order[1:]
                val = pymongo.DESCENDING
            ordering[key] = val
        return ordering

    def clone(self):
        return QuerySet(self.document, self._filters, self._ordering)

    def get_items(self):
        """
        Returns pymongo result set.
        """
        items =self.document.objects.collection.find(self.get_filters())
        ordering = self.get_ordering()
        if ordering:
            items = items.sort(ordering.items())
        if self.offset:
            items.skip(self.offset)
        if self.limit:
            items.limit(self.limit)
        return items

    def pluck(self, key, default=None):
        for item in self.get_items():
            yield item.get(key, None)

    def count(self):
        return self.get_items().count()

    def add_filters(self, **filters):
        self._filters.update(filters)

    def filter(self, **filters):
        queryset = self.clone()
        queryset.add_filters(**filters)
        return queryset

    def add_ordering(self, ordering):
        if ordering not in self._ordering:
            self._ordering.append(ordering)

    def order_by(self, ordering):
        queryset = self.clone()
        queryset.add_ordering(ordering)
        return queryset

