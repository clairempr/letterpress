from django_date_extensions.fields import ApproximateDate
from unittest.mock import patch

from django.db import connection
from django.db.models.base import ModelBase
from django.test import TestCase

from letters.models import Document, DocumentImage
from letters.tests.factories import CorrespondentFactory, DocumentImageFactory, DocumentSourceFactory


class DocumentTestCase(TestCase):
    """
    Test Document model. It's abstract and using a factory object gives an error,
    so create a temporary test model

    https://stackoverflow.com/questions/49569239/how-to-call-parent-class-methods-in-python
    https://stackoverflow.com/questions/50248330/django-unit-testing-how-should-one-test-abstract-models
    """

    model = Document

    @classmethod
    def setUpClass(cls):
        # Create a dummy model
        cls.model = ModelBase(
            '__TestModel__' + cls.model.__name__, (cls.model,),
            {'__module__': cls.model.__module__}
        )

        # Create the schema for our test model
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls.model)

    @classmethod
    def tearDownClass(cls):
        # Delete the schema for the test model
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls.model)

    def setUp(self):
        self.source = DocumentSourceFactory()
        self.writer = CorrespondentFactory()
        self.test_document = self.model.objects.create(source=self.source,
                                                       writer=self.writer)

    def test_get_display_string(self):
        """
        Document.get_display_string() should return 'Define "get_display_string" in %(class)s'
        """

        expected = 'Define "get_display_string" in %(class)s'

        self.assertEqual(str(self.test_document), expected,
                         "Document.get_display_string() should return '{}'".format(expected))

    @patch.object(Document, 'get_display_string', autospec=True)
    def test__str__(self, mock_get_display_string):
        """
        Document.__str__() should return Document.get_display_string()
        """

        mock_get_display_string.return_value = 'display str'

        document_str = str(self.test_document)
        self.assertEqual(document_str, mock_get_display_string.return_value,
                         'Document.__str__() should return value of Document.get_display_string()')

    @patch.object(Document, 'get_display_string', autospec=True)
    def test_to_string(self, mock_get_display_string):
        """
        Document.to_string() should return Document.get_display_string()
        """

        mock_get_display_string.return_value = 'display str'

        self.assertEqual(self.test_document.to_string(), mock_get_display_string.return_value,
                         'Document.to_string() should return value of Document.get_display_string()')

    @patch('letters.models.document.get_image_preview', autospec=True)
    def test_image_preview(self, mock_get_image_preview):
        """
        Document.image_preview() should return Document.get_image_preview()
        """

        mock_get_image_preview.return_value = 'image_preview'

        self.assertEqual(self.test_document.image_preview(), mock_get_image_preview.return_value,
                         'Document.image_preview() should return value of Document.get_image_preview()')

    def test_image_tags(self):
        """
        Document.image_tags() should return a list of image_tag() for its DocumentImages
        """

        # Add DocumentImages to the Document using a mock instead of images.add() because that
        # causes an error AttributeError: 'ManyToManyField' object has no attribute 'm2m_field_name'
        # Actual use of images on classes that inherit from Document works fine, so just patch here
        # because it may just be caused by direct use of an abstract class (Document)
        with patch.object(self.model, 'images', autospec=True) as mock_document_images:
            mock_document_images.all.return_value = [DocumentImageFactory(), DocumentImageFactory()]

            expected_image_tags = ['image_tag1', 'image_tag2']
            with patch.object(DocumentImage, 'image_tag', autospec=True, side_effect=expected_image_tags):
                image_tags = self.test_document.image_tags()

                for expected_image_tag in expected_image_tags:
                    self.assertIn(expected_image_tag, image_tags,
                                  'Document.image_tags() value should contain image_tag for its DocumentImage')

    def test_list_date(self):
        """
        Document.list_date() should return formatted date with separators and unknown elements filled with '?'

        ApproximateDateField won't allow a date without a year, or a date with just a year and a day,
        so don't bother with those
        """

        # If no date, list_date() should return '(Undated)'
        expected = '(Undated)'
        self.assertEqual(self.test_document.list_date(), expected,
                         "If no date, Document.list_date() should return '{}'".format(expected))

        # If year only, list_date() should return year-??-??
        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864))
        expected = '1864-??-??'
        self.assertEqual(document.list_date(), expected,
                         "If year only, Document.list_date() should return '{}'".format(expected))

        # If year and month only, list_date() should return year-month-??
        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6))
        expected = '1864-06-??'
        self.assertEqual(document.list_date(), expected,
                         "If year and month only, Document.list_date() should return '{}'".format(expected))

        # If year, month, and day, list_date() should return year-month-day
        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6, 15))
        expected = '1864-06-15'
        self.assertEqual(document.list_date(), expected,
                         "If year, month, and day, Document.list_date() should return '{}'".format(expected))

    def test_sort_date(self):
        """
        sort_date() should return date in the format yyyymmdd with zeroes in unknown elements
        """

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864))
        expected = '18640000'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year only, Document.sort_date() should return '{}'".format(expected))

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6))
        expected = '18640600'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year and month only, Document.sort_date() should return '{}'".format(expected))

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6, 15))
        expected = '18640615'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year, month, and day, Document.sort_date() should return '{}'".format(expected))

    def test_index_date(self):
        """
        index_date() should return date in the format yyyy-MM-dd or yyyy-MM or yyyy for elasticsearch index
        """

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864))
        expected = '1864'
        self.assertEqual(document.index_date(), expected,
                         "If date with year only, Document.index_date() should return '{}'".format(expected))

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6))
        expected = '1864-06'
        self.assertEqual(document.index_date(), expected,
                         "If date with year and month only, Document.sort_date() should return '{}'".format(expected))

        document = self.model.objects.create(source=self.source, writer=self.writer,
                                             date=ApproximateDate(1864, 6, 15))
        expected = '1864-06-15'
        self.assertEqual(document.index_date(), expected,
                         "If date with year, month, and day, Document.index_date() should return '{}'".format(expected))
