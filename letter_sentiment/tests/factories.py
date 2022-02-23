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
