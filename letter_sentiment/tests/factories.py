from factory import SubFactory
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

    class Meta:
        model = Term
