from unittest.mock import patch

from factory import post_generation, SubFactory
from factory.django import DjangoModelFactory

from letter_sentiment.models import CustomSentiment, Term


class CustomSentimentFactory(DjangoModelFactory):
    """
    Base CustomSentiment factory
    """

    class Meta:
        model = CustomSentiment


class TermFactory(DjangoModelFactory):
    """
    Base Term factory
    """

    custom_sentiment = SubFactory(CustomSentimentFactory)
    # Can't figure out to reference to __original_text in unit test
    __original_text = None

    class Meta:
        model = Term

    @classmethod
    @patch('letter_sentiment.models.analyze_text', autospec=True)
    def _create(cls, model_class, mock_analyze_text, *args, **kwargs):
        """
        Mock analyze_text() so a term doesn't actually get analyzed with Elasticsearch
        """

        obj = model_class(*args, **kwargs)
        obj.analyzed_text = obj.text
        obj.save()
        return obj
