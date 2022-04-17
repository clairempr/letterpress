from django.test import RequestFactory, TestCase

from letters.mixins import ObjectNotFoundMixin
from letters.models import Letter


class ObjectNotFoundMixinTestCase(TestCase):
    """
    ObjectNotFoundMixin.dispatch() should return rendered html giving details about the object that wasn't found
    """

    def test_dispatch(self):
        request = RequestFactory()
        mixin = ObjectNotFoundMixin()
        mixin.model = Letter
        mixin.queryset = Letter.objects.all()
        mixin.request = request
        mixin.kwargs = {'pk': 1}

        response = mixin.dispatch(request)

        self.assertTrue('<title>Letter not found</title>' in str(response.content),
                        "ObjectNotFoundMixin response content should include '<object_type> not found'")
        self.assertTrue('ID 1' in str(response.content),
                        "ObjectNotFoundMixin response content should include 'ID <object_id>' if it's for a letter")
