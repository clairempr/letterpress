from django.http import Http404
from django.shortcuts import render
from django.views.generic.detail import SingleObjectMixin


class ObjectNotFoundMixin(SingleObjectMixin):

    def dispatch(self, request, *args, **kwargs):
        pk = self.kwargs.get(self.pk_url_kwarg)
        try:
            self.get_object()
        except Http404:
            object_type = self.model.__name__
            return object_not_found(self.request, pk, object_type)

        return super().dispatch(request, *args, **kwargs)


def object_not_found(request, pk, object_type):
    return render(request, 'obj_not_found.html',
                  {'title': object_type + ' not found', 'object_id': pk, 'object_type': object_type})
