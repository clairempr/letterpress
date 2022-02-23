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
        self.request_factory = RequestFactory()

    def get_changelist(self, request, model, modeladmin):
        """
        This is for Django 1.11.1 through ???
        (copied straight from Django 1.11.1 admin filter unit test setup)
        https://github.com/django/django/blob/aab5deb53eccc2ac1c36106c91864b0aaf48f5a8/tests/admin_filters/tests.py#L296

        For Django 2x+, it can be replaced by
            changelist = self.modeladmin.get_changelist_instance(request)
        """
        return ChangeList(
            request, model, modeladmin.list_display,
            modeladmin.list_display_links, modeladmin.list_filter,
            modeladmin.date_hierarchy, modeladmin.search_fields,
            modeladmin.list_select_related, modeladmin.list_per_page,
            modeladmin.list_max_show_all, modeladmin.list_editable, modeladmin,
        )

    def test_lookups(self):
        """
        All lowercase and capital letters should be present in lookups in tuples of (lower, upper)
        """
        request = self.request_factory.get('/')
        filter = FirstLetterFilter(request, params='', model=Term, model_admin=self.modeladmin)
        expected = [(letter.lower(), letter) for letter in list(ascii_uppercase)]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    def test_queryset(self):
        """
        queryset() should return Term objects whose text starts with 'first letter' if one specified
        otherwise it should return all Term objects
        """
        user = AnonymousUser()

        horse = TermFactory(text='horse')
        pony = TermFactory(text='pony')

        request = self.request_factory.get('/')
        request.user = user
        changelist = self.get_changelist(request, Term, self.modeladmin)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertSetEqual(set(queryset), set([horse, pony]))

        # Look for terms that start with p
        request = self.request_factory.get('/', {'term': 'p'})
        request.user = user
        changelist = self.get_changelist(request, Term, self.modeladmin)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
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

        # analyzed_text is different from  text
        term = TermFactory(text=text, analyzed_text=analyzed_text)
        expected_html = str.format('<span style="color:red;">{0}</span>', analyzed_text)
        analyzed_text_display = TermInline.analyzed_text_display(self, term)
        self.assertIn(analyzed_text, expected_html,
                      "analyzed_text_display() should return Term's analyzed_text if it's not equal to text")
