from unittest.mock import patch

from django.contrib.admin import site
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.test import RequestFactory, TestCase

from letters.admin import LetterAdmin
from letters.models import Letter
from letters.tests.factories import LetterFactory

User = get_user_model()


class LetterAdminTestCase(TestCase):

    @patch.object(Letter, 'delete', autospec=True)
    def test_delete_queryset(self, mock_delete):
        """
        delete_queryset() should override Django Admin's delete_queryset action
        to use model's delete method and update elasticsearch index
        """
        modeladmin = LetterAdmin(Letter, site)

        # First an empty queryset
        queryset = Letter.objects.all()
        modeladmin.delete_queryset(RequestFactory(), queryset)

        self.assertEqual(mock_delete.call_count, 0,
                         "delete_selected() shouldn't delete anything if queryset empty")

        # Now a queryset with objects
        LetterFactory()
        LetterFactory()

        queryset = Letter.objects.all()
        modeladmin.delete_queryset(RequestFactory(), queryset)

        self.assertEqual(mock_delete.call_count, 2,
                         'delete_queryset() should delete all objects in queryset')


class LetterAdminFormTestCase(TestCase):

    def test_get_form(self):
        """
        get_form() should return a form with custom styling
        """
        modeladmin = LetterAdmin(Letter, site)
        # Set up superuser to log in to admin and be able to create new Employees
        user = User.objects.create_superuser('admin', 'admin@example.com', 'Password123')
        request = RequestFactory()
        request.user = user

        form = modeladmin.get_form(request=request, obj=LetterFactory())

        # Make sure form fields have height set
        for field in ['heading', 'greeting', 'closing', 'signature', 'ps']:
            self.assertIn('height', form.base_fields[field].widget.attrs['style'],
                          "LetterAdmin form should have height set for field'{}'" )
