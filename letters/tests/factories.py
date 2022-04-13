from factory import BUILD_STRATEGY, Faker, SubFactory
from factory.django import DjangoModelFactory
from unittest.mock import patch

from letters.models import Correspondent, Document, DocumentImage, DocumentSource, Envelope, Letter, MiscDocument, Place


class CorrespondentFactory(DjangoModelFactory):
    """
    Base Correspondent factory
    """

    last_name = Faker('last_name')
    first_names = Faker('first_name')

    class Meta:
        model = Correspondent


class DocumentSourceFactory(DjangoModelFactory):
    """
    Base DocumentSource factory
    """

    class Meta:
        model = DocumentSource


class PlaceFactory(DjangoModelFactory):
    """
    Base Place factory
    """

    class Meta:
        model = Place


class DocumentFactory(DjangoModelFactory):
    """
    Base Document factory
    """

    source = SubFactory(DocumentSourceFactory)
    writer = SubFactory(CorrespondentFactory)

    class Meta:
        model = Document
        abstract = True


class EnvelopeFactory(DocumentFactory):
    """
    Base Envelope factory
    """

    recipient = SubFactory(CorrespondentFactory)
    origin = SubFactory(PlaceFactory)
    destination = SubFactory(PlaceFactory)

    class Meta:
        model = Envelope


class LetterFactory(DocumentFactory):
    """
    Base Letter factory
    """

    place = SubFactory(PlaceFactory)
    recipient = SubFactory(CorrespondentFactory)

    class Meta:
        model = Letter

    @classmethod
    @patch.object(Letter, 'create_or_update_in_elasticsearch', autospec=True)
    def _create(cls, model_class, mock_create_or_update_in_elasticsearch, *args, **kwargs):
        """
        Mock create_or_update_in_elasticsearch() so a letter doesn't actually get indexed
        """

        obj = model_class(*args, **kwargs)
        obj.save()
        return obj


class MiscDocumentFactory(DocumentFactory):
    """
    Base MiscDocument factory
    """

    place = SubFactory(PlaceFactory)

    class Meta:
        model = MiscDocument


class DocumentImageFactory(DjangoModelFactory):
    """
    Base DocumentImage factory
    """

    class Meta:
        model = DocumentImage


class BuildOnlyDocumentImageFactory(DjangoModelFactory):
    """
    Base DocumentImage factory using build strategy - not persisted to test database
    """

    class Meta:
        model = DocumentImage
        strategy = BUILD_STRATEGY
