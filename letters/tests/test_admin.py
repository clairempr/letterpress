from unittest.mock import patch

from django.contrib.admin import site
from django.db.models import Model
from django.test import RequestFactory, TestCase

from letters.admin import delete_selected, LetterAdmin
from letters.models import Letter
from letters.tests.factories import LetterFactory


class DeleteSelectedTestCase(TestCase):
    """
    delete_selected() should override Django Admin's delete_selected action
    to use model's delete method and update elasticsearch index
    """

    @patch.object(Letter, 'delete', autospec=True)
    def test_delete_selected(self, mock_delete):
        modeladmin = LetterAdmin(Letter, site)

        # First an empty queryset
        queryset = Letter.objects.all()
        delete_selected(modeladmin, RequestFactory(), queryset)

        self.assertEqual(mock_delete.call_count, 0,
                         "delete_selected() shouldn't delete anything if queryset empty")

        # Now a queryset with objects
        LetterFactory()
        LetterFactory()

        queryset = Letter.objects.all()
        delete_selected(modeladmin, RequestFactory(), queryset)

        self.assertEqual(mock_delete.call_count, 2,
                         'delete_selected() should delete all objects in queryset')
