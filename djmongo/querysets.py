from django.utils.datastructures import SortedDict
from djmongo.exceptions import MultipleItemsReturnedError
import pymongo
import re


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

    def __len__(self):
        return self.count()

    def get_filters(self):
        for key in (k for k in self._filters if '__' in k):
            field, operator = key.split('__', 1)
            if operator == 'in':
                self._filters[field] = {'$in': list(self._filters.pop(key))}
            elif operator in ['gt', 'gte', 'lt', 'lte']:
                self._filters[field] = {'$' + operator: self._filters.pop(key)}
            elif operator in ['contains', 'icontains']:
                pat = r'.*%s.*' % self._filters.pop(key)
                if operator[0] == 'i':
                    pattern = re.compile(pat, re.IGNORECASE)
                else:
                    pattern = re.compile(pat)
                self._filters[field] = pattern

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
        queryset = QuerySet(self.document, self._filters, self._ordering)
        queryset.offset = self.offset
        queryset.limit = self.limit
        return queryset

    def all(self):
        return self

    def get_items(self):
        """
        Returns pymongo result set.
        """
        items = self.document.objects.collection.find(self.get_filters())
        ordering = self.get_ordering()
        if ordering:
            items = items.sort(ordering.items())
        if self.offset:
            items.skip(self.offset)
        if self.limit:
            items.limit(self.limit)
        return items

    def pluck(self, *keys):
        for item in self.get_items():
            if len(keys) == 1:
                yield item.get(keys[0], None)
            else:
                yield tuple(item.get(key) for key in keys)

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

    def get(self, **filters):
        result = None
        for item in self.filter(**filters):
            if result is not None:
                raise MultipleItemsReturnedError("More than one item found "
                    "for filters: %r" % filters)
            else:
                result = item
        if result is None:
            raise self.document.DoesNotExist("No item found for filters: %r"
                % filters)
        return result

    @property
    def model(self):
        return self.document

