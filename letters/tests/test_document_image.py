from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.test import TestCase

from letters.models import DocumentImage
from letters.tests.factories import BuildOnlyDocumentImageFactory, DocumentImageFactory


class DocumentImageTestCase(TestCase):
    """
    Test DocumentImage model
    """

    def setUp(self):
        self.filename = 'image.jpg'

        # Mock the file in DocumentImage.image_file so that image_file.name is set and accessible
        self.file_mock = MagicMock(spec=File)
        self.file_mock.name = self.filename

        # Mock Django Storage to avoid creating a real file
        self.storage_mock = MagicMock(spec=Storage, name='StorageMock')
        self.storage_mock.save.return_value.name = self.filename

    def test__str__(self):
        """
        DocumentImage.__str__() should return DocumentImage.description if there is one
        Otherwise it should return the image filename
        """

        # Mock storage system is used so we don't touch the filesystem
        with patch('django.core.files.storage.default_storage._wrapped', self.storage_mock):
            # If there's no description, str should contain the filename
            # Use a factory object that won't be persisted to test database because that causes the error
            # "TypeError: __str__ returned non-string (type MagicMock)", starting with Django 2.0
            document_image = BuildOnlyDocumentImageFactory(image_file=self.file_mock)
            self.assertIn(self.filename, str(document_image),
                          "If there's no description, DocumentImage str should contain the filename")

            # If there's a description, str should be the description
            document_image = DocumentImageFactory(description='image of letter')
            self.assertEqual(str(document_image), document_image.description,
                             "If there's a description, DocumentImage str should be the description")

    def test_get_url(self):
        """
        DocumentImage.get_url() should include settings.MEDIA_URL and self.image_file.name
        """

        # Mock storage system is used so we don't touch the filesystem
        with patch('django.core.files.storage.default_storage._wrapped', self.storage_mock):
            # Use a factory object that won't be persisted to test database because that causes the error
            # "TypeError: __str__ returned non-string (type MagicMock)", starting with Django 2.0
            document_image = BuildOnlyDocumentImageFactory(image_file=self.file_mock)
            url = document_image.get_url()
            self.assertIn(settings.MEDIA_URL, url, 'DocumentImage.get_url() should include settings.MEDIA_URL')
            self.assertIn(document_image.image_file.name, url, 'DocumentImage.get_url() should include image_file.name')

    @patch.object(DocumentImage, 'image_preview_with_link', autospec=True)
    def test_image_tag(self, mock_image_preview_with_link):
        """
        DocumentImage.image_tag() should call image_preview_with_link(400)
        """

        document_image = DocumentImageFactory()
        document_image.image_tag()
        args, kwargs = mock_image_preview_with_link.call_args
        self.assertEqual(args, (document_image, 400),
                         'DocumentImage.image_tag() should call image_preview_with_link(400)')

    @patch.object(DocumentImage, 'image_preview_with_link', autospec=True)
    def test_thumbnail(self, mock_image_preview_with_link):
        """
        DocumentImage.thumbnail() should call image_preview_with_link(100)
        """

        document_image = DocumentImageFactory()
        document_image.thumbnail()
        args, kwargs = mock_image_preview_with_link.call_args
        self.assertEqual(args, (document_image, 100),
                         'DocumentImage.thumbnail() should call image_preview_with_link(100)')

    @patch.object(DocumentImage, 'get_url', autospec=True)
    def test_image_preview_with_link(self, mock_get_url):
        """
        DocumentImage.image_preview_with_link() should include link to image file if there is one
        Otherwise it should return "No image"
        """

        mock_get_url.return_value = 'image url'

        # Mock storage system is used so we don't touch the filesystem
        with patch('django.core.files.storage.default_storage._wrapped', self.storage_mock):
            # If there's an image file, image_preview_with_link() should include get_url()
            # Use a factory object that won't be persisted to test database because that causes the error
            # "TypeError: __str__ returned non-string (type MagicMock)", starting with Django 2.0
            document_image = BuildOnlyDocumentImageFactory(image_file=self.file_mock)
            image_preview_with_link = document_image.image_preview_with_link(100)
            self.assertEqual(mock_get_url.call_count, 2,
                             'DocumentImage.image_preview_with_link() should call DocumentImage.get_url() twice')
            self.assertIn(mock_get_url.return_value, image_preview_with_link,
                          'DocumentImage.image_preview_with_link() should include DocumentImage.get_url()')

            # If there's no image file, image_preview_with_link() should return 'No image'
            document_image = DocumentImageFactory()
            image_preview_with_link = document_image.image_preview_with_link(100)
            expected = 'No image'
            self.assertEqual(image_preview_with_link, expected,
                "If there's no image file, DocumentImage.image_preview_with_link() should return {}".format(expected))
