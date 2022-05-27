from string import ascii_uppercase

from django.contrib.admin import site
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from letter_sentiment.models import Term
from letter_sentiment.admin import FirstLetterFilter, TermAdmin, TermInline
from letter_sentiment.tests.factories import TermFactory


class FirstLetterFilterTestCase(TestCase):
    """
    Test list filter for first letter of term
    """

    def setUp(self):
        self.modeladmin = TermAdmin(Term, site)
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()

    def test_lookups(self):
        """
        All lowercase and capital letters should be present in lookups in tuples of (lower, upper)
        """

        filter = FirstLetterFilter(self.request, params={}, model=Term, model_admin=self.modeladmin)
        expected = [(letter.lower(), letter) for letter in list(ascii_uppercase)]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    def test_queryset(self):
        """
        queryset() should return Term objects whose text starts with 'first letter' if one specified
        otherwise it should return all Term objects
        """

        horse = TermFactory(text='horse')
        pony = TermFactory(text='pony')

        # If no first letter specified, all Terms should be returned
        filter = FirstLetterFilter(self.request, params={}, model=Term, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Term.objects.all())
        self.assertSetEqual(set(queryset), set([horse, pony]))

        # Look for terms that start with p
        filter = FirstLetterFilter(self.request, params={'term': 'p'}, model=Term, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Term.objects.all())
        self.assertSetEqual(set(queryset), set([pony]))


class TermInlineTestCase(TestCase):
    """
    Test TermInline
    """

    def test_analyzed_text_display(self):
        """
        If Term's analyzed_text is the same as its text, analyzed_text_display() should return that value
        Otherwise it should return an html span with analyzed text in red
        """

        text = 'chasteneth'
        analyzed_text = 'chasten'

        # analyzed_text is the same as text
        term = TermFactory(text=text, analyzed_text=text)
        self.assertEqual(TermInline.analyzed_text_display(self, term), text,
                         "analyzed_text_display() should return Term's text if it's equal to analyzed text")

        # analyzed_text is different from text
        term = TermFactory(text=text)
        # Manually set analyzed_text to be different, because factory objects sets it equal to text
        term.analyzed_text = analyzed_text
        expected_html = str.format('<span style="color:red;">{0}</span>', analyzed_text)
        analyzed_text_display = TermInline.analyzed_text_display(self, term)
        self.assertIn(analyzed_text_display, expected_html,
                      "analyzed_text_display() should return Term's analyzed_text if it's not equal to text")
