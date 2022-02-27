from factory import SubFactory
from factory.django import DjangoModelFactory
from unittest.mock import patch

from letters.models import Correspondent, Document, DocumentSource, Letter, Place


class CorrespondentFactory(DjangoModelFactory):
    """
    Base Correspondent factory
    """

    class Meta:
        model = Correspondent


class DocumentSourceFactory(DjangoModelFactory):
    """
    Base DocumentSource factory
    """

    class Meta:
        model = DocumentSource


class DocumentFactory(DjangoModelFactory):
    """
    Base Document factory
    """

    source = SubFactory(DocumentSourceFactory)
    writer = SubFactory(CorrespondentFactory)


    class Meta:
        model = Document


class PlaceFactory(DjangoModelFactory):
    """
    Base Place factory
    """

    class Meta:
        model = Place


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
    def _create(cls, model_class, mock_create_or_update_in_elasticsearch,
                *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.save()
        return obj
