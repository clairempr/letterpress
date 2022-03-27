from django_date_extensions.fields import ApproximateDate
from unittest.mock import patch

from django.test import TestCase

from letters.models import Document


class DocumentTestCase(TestCase):
    """
    Test Document model. It's abstract and using a factory object gives an error,
    but using an actual Document object works
    """

    def test_get_display_string(self):
        """
        Document.get_display_string() should return 'Define "get_display_string" in %(class)s'
        """

        expected = 'Define "get_display_string" in %(class)s'

        self.assertEqual(str(Document()), expected,
                         "Document.get_display_string() should return '{}'".format(expected))

    @patch.object(Document, 'get_display_string', autospec=True)
    def test__str__(self, mock_get_display_string):
        """
        Document.__str__() should return Document.get_display_string()
        """

        mock_get_display_string.return_value = 'display str'

        document_str = str(Document())
        self.assertEqual(document_str, mock_get_display_string.return_value,
                         'Document.__str__() should return value of Document.get_display_string()')

    @patch.object(Document, 'get_display_string', autospec=True)
    def test_to_string(self, mock_get_display_string):
        """
        Document.to_string() should return Document.get_display_string()
        """

        mock_get_display_string.return_value = 'display str'

        self.assertEqual(Document().to_string(), mock_get_display_string.return_value,
                         'Document.to_string() should return value of Document.get_display_string()')

    @patch('letters.models.document.get_image_preview', autospec=True)
    def test_image_preview(self, mock_get_image_preview):
        """
        Document.image_preview() should return Document.get_image_preview()
        """

        mock_get_image_preview.return_value = 'image_preview'

        self.assertEqual(Document().image_preview(), mock_get_image_preview.return_value,
                         'Document.image_preview() should return value of Document.get_image_preview()')

    def test_list_date(self):
        """
        Document.list_date() should return formatted date with separators and unknown elements filled with '?'

        ApproximateDateField won't allow a date without a year, or a date with just a year and a day,
        so don't bother with those
        """

        # If no date, list_date() should return '(Undated)'
        expected = '(Undated)'
        self.assertEqual(Document().list_date(), expected,
                         "If no date, Document.list_date() should return '{}'".format(expected))

        # If year only, list_date() should return year-??-??
        document = Document(date=ApproximateDate(1864))
        expected = '1864-??-??'
        self.assertEqual(document.list_date(), expected,
                         "If year only, Document.list_date() should return '{}'".format(expected))

        # If year and month only, list_date() should return year-month-??
        document = Document(date=ApproximateDate(1864, 6))
        expected = '1864-06-??'
        self.assertEqual(document.list_date(), expected,
                         "If year and month only, Document.list_date() should return '{}'".format(expected))

        # If year, month, and day, list_date() should return year-month-day
        document = Document(date=ApproximateDate(1864, 6, 15))
        expected = '1864-06-15'
        self.assertEqual(document.list_date(), expected,
                         "If year, month, and day, Document.list_date() should return '{}'".format(expected))

    def test_sort_date(self):
        """
        sort_date() should return date in the format yyyymmdd with zeroes in unknown elements
        """

        document = Document(date=ApproximateDate(1864))
        expected = '18640000'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year only, Document.sort_date() should return '{}'".format(expected))

        document = Document(date=ApproximateDate(1864, 6))
        expected = '18640600'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year and month only, Document.sort_date() should return '{}'".format(expected))

        document = Document(date=ApproximateDate(1864, 6, 15))
        expected = '18640615'
        self.assertEqual(document.sort_date(), expected,
                         "If date with year, month, and day, Document.sort_date() should return '{}'".format(expected))

    def test_index_date(self):
        """
        index_date() should return date in the format yyyy-MM-dd or yyyy-MM or yyyy for elasticsearch index
        """

        document = Document(date=ApproximateDate(1864))
        expected = '1864'
        self.assertEqual(document.index_date(), expected,
                         "If date with year only, Document.index_date() should return '{}'".format(expected))

        document = Document(date=ApproximateDate(1864, 6))
        expected = '1864-06'
        self.assertEqual(document.index_date(), expected,
                         "If date with year and month only, Document.sort_date() should return '{}'".format(expected))

        document = Document(date=ApproximateDate(1864, 6, 15))
        expected = '1864-06-15'
        self.assertEqual(document.index_date(), expected,
                         "If date with year, month, and day, Document.index_date() should return '{}'".format(expected))
