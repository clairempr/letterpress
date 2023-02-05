from unittest.mock import patch

from django.test import TestCase

from letters.tests.factories import DocumentSourceFactory


class DocumentSourceTestCase(TestCase):
    """
    Test DocumentSource model
    """

    def test__str__(self):
        """
        DocumentSource.__str__() should return DocumentSource.name
        """

        document_source = DocumentSourceFactory(name='My Documents')
        self.assertEqual(str(document_source), document_source.name,
                         'DocumentSource.__str__() should return DocumentSource.name')

    def test__lt__(self):
        """
        DocumentSource.__lt__() should return True if self.to_string()
        comes before other document_source.to_string() in alphabetic sorting,
        otherwise it should return False
        """

        my_documents = DocumentSourceFactory(name='My Documents')
        my_other_documents = DocumentSourceFactory(name='My Documents')
        your_documents = DocumentSourceFactory(name='Your Documents')

        self.assertTrue(my_documents < your_documents, '{} should be < {}'.format(my_documents, your_documents))
        self.assertFalse(my_documents < my_other_documents,
                         "{} shouldn't be be < {}".format(my_documents, my_other_documents))
        self.assertFalse(your_documents < my_documents,
                         "{} shouldn't be be < {}".format(your_documents, my_documents))

    def test_to_string(self):
        """
        DocumentSource.to_string() should return DocumentSource.name
        """

        document_source = DocumentSourceFactory(name='My Documents')
        self.assertEqual(document_source.to_string(), document_source.name,
                         'DocumentSource.to_string() should return DocumentSource.name')

    @patch('letters.models.document_source.get_image_preview', autospec=True)
    def test_image_preview(self, mock_get_image_preview):
        """
        DocumentSource.image_preview() should return DocumentSource.get_image_preview()
        """

        mock_get_image_preview.return_value = 'image_preview'

        self.assertEqual(DocumentSourceFactory().image_preview(), mock_get_image_preview.return_value,
                         'DocumentSource.image_preview() should return value of DocumentSource.get_image_preview()')
