from collections import namedtuple
from django_date_extensions.fields import ApproximateDate

from django.contrib.gis.geos import Point
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from letters.tests.factories import CorrespondentFactory, DocumentSourceFactory, LetterFactory, PlaceFactory


def get_initial_filter_values():
    Sentiment = namedtuple('Sentiment', ['id', 'name'])
    sentiments = [Sentiment(id=123, name='Positive/negative')]
    initial_filter_values = {
        'sources': [],
        'writers': [],
        'start_date': '1863-01-01',
        'end_date': '1863-12-31',
        'words': ['oddment', 'tweak'],
        'sentiments': sentiments
    }
    return initial_filter_values


class ChartTemplateSnippetTestCase(SimpleTestCase):
    """
    Test chart template snippet
    """

    def test_template_content(self):
        template = 'snippets/chart.html'
        script = 'This is the script'
        div = 'This is the div'

        rendered = render_to_string(template, context={'script': script, 'divs': [div]})

        self.assertIn(script, rendered, 'script should be in HTML')
        self.assertIn(div, rendered, 'div should be in HTML')


class FilterTemplateSnippetTestCase(TestCase):
    """
    Test filter template snippet
    """

    def test_template_content(self):
        template = 'snippets/filter.html'

        source = DocumentSourceFactory(id=123, name='Letters I found in a mysterious locked drawer')
        writer = CorrespondentFactory()
        initial_filter_values = get_initial_filter_values()
        initial_filter_values['sources'] = [source]
        initial_filter_values['writers'] = [writer]

        rendered = render_to_string(template, context={'filter_values': initial_filter_values})

        # Sources should be in HTML
        self.assertIn('Sources', rendered, "'Sources' should be in HTML")
        self.assertIn(str(source.id), rendered, "Source ID from filter should be in HTML")
        self.assertIn(str(source), rendered, "Source from filter should be in HTML")

        # Writers should be in HTML
        self.assertIn('Writers', rendered, "'Writers' should be in HTML")
        self.assertIn(str(writer.id), rendered, "Writer ID from filter should be in HTML")
        self.assertIn(str(writer), rendered, "Writer from filter should be in HTML")

        # Start date should be in HTML
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(initial_filter_values.get('start_date'), rendered, "Start date from filter should be in HTML")

        # End date should be in HTML
        self.assertIn('End date', rendered, "'End date' should be in HTML")
        self.assertIn(initial_filter_values.get('end_date'), rendered, "End date from filter should be in HTML")

        # If show_search_text is True, then 'Search text' should be in HTML and words shouldn't be
        rendered = render_to_string(
            template, context={'filter_values': initial_filter_values, 'show_search_text': True}
        )
        self.assertIn('Search text', rendered, "If show_search_text in context, then 'Search text' should be in HTML")
        for word in initial_filter_values.get('words'):
            self.assertNotIn(word, rendered, "If show_search_text in context, then words shouldn't be shown")

        # If show_words is True, then words should be in HTML and 'Search text' shouldn't be
        rendered = render_to_string(template, context={'filter_values': initial_filter_values, 'show_words': True})
        self.assertNotIn('Search text', rendered, "If show_words in context, then 'Search text' shouldn't be in HTML")
        for word in initial_filter_values.get('words'):
            self.assertIn(word, rendered, "If show_words in context, then words should be shown")

        # If show_sentiment in context, sentiment_dropdown.html should be include
        # Just spot-check here
        rendered = render_to_string(template, context={'filter_values': initial_filter_values, 'show_sentiment': True})
        self.assertIn('Sentiments', rendered, "If show_sentiment in context, then 'Sentiments' should be in HTML")
        rendered = render_to_string(template, context={'filter_values': initial_filter_values})
        self.assertNotIn('Sentiments', rendered,
                         "If show_sentiment not in context, then 'Sentiments' shouldn't be in HTML")

        # If sort_by in context, sort_by_dropdown.html should be include
        # Just spot-check here
        rendered = render_to_string(template, context={'filter_values': initial_filter_values,
                                                       'sort_by': [('DATE', 'Date')]})
        self.assertIn('Sort by', rendered, "If sort_by in context, then 'Sort by' should be in HTML")
        rendered = render_to_string(template, context={'filter_values': initial_filter_values})
        self.assertNotIn('Sort by', rendered,
                         "If sort_by not in context, then 'Sort by' shouldn't be in HTML")

        # If show_export_button in context, export_text and export_csv buttons should be in HTML
        rendered = render_to_string(template, context={'filter_values': initial_filter_values,
                                                       'show_export_button': True})
        self.assertIn('export_text', rendered,
                      "If show_export_button in context, then 'export_text' button should be in HTML")
        self.assertIn('export_csv', rendered,
                      "If show_export_button in context, then 'export_csv' button should be in HTML")
        rendered = render_to_string(template, context={'filter_values': initial_filter_values})
        self.assertNotIn('export_text', rendered,
                         "If show_export_button not in context, then 'export_text' button shouldn't be in HTML")
        self.assertNotIn('export_csv', rendered,
                         "If show_export_button not in context, then 'export_csv' button shouldn't be in HTML")


class LetterContentsTemplateSnippetTestCase(TestCase):
    """
    Test letter contents template snippet
    """

    def test_template_content(self):
        template = 'snippets/letter_contents.html'
        letter = LetterFactory(
            heading='Januery the 1st / 62',
            greeting='Miss Evey',
            body='As this is the beginin of a new year I thought as I was a lone to night I would write you '
                 'a few lines to let you know that we are not all ded yet.',
            closing='your friend as every',
            signature='F.P. Black',
            ps='p.s. remember me to all'
        )

        rendered = render_to_string(template, context={'letter': letter})

        self.assertIn(letter.heading, rendered, 'HTML should contain heading')
        self.assertIn(letter.greeting, rendered, 'HTML should contain greeting')
        self.assertIn(letter.body, rendered, 'HTML should contain body')
        self.assertIn(letter.closing, rendered, 'HTML should contain closing')
        self.assertIn(letter.signature, rendered, 'HTML should contain signature')
        self.assertIn(letter.ps, rendered, 'HTML should contain ps')


class MapTemplateSnippetTestCase(TestCase):
    """
    Test map template snippet
    """

    def test_template_content(self):
        template = 'snippets/map.html'
        place = PlaceFactory(name='Manassas Junction', state='Virginia', point=Point(12.34, 56.78),
                             notes='https://en.wikipedia.org/wiki/Manassas,_Virginia')

        rendered = render_to_string(template, context={'places': [place]})

        self.assertIn(str(place), rendered, 'HTML should contain place')
        self.assertIn(str(place.id), rendered, 'HTML should contain place ID')
        self.assertIn(str(place.point.x), rendered, "Place's x-coordinate should appear in HTML")
        self.assertIn(str(place.point.y), rendered, "Place's y-coordinate should appear in HTML")
        self.assertIn('map_init', rendered, "'map_init' should appear in HTML")


class NavigationTemplateSnippetTestCase(SimpleTestCase):
    """
    Test navigation template snippet
    """

    def test_template_content(self):
        template = 'snippets/navigation.html'
        rendered = render_to_string(template)

        self.assertIn('navbar', rendered, "'navbar' should appear in HTML")
        self.assertIn('Toggle navigation', rendered, "'Toggle navigation' should appear in HTML")
        self.assertIn('Home', rendered, "'Letterpress' should appear in HTML")
        self.assertIn('writing-hand.png', rendered, "'writing-hand.png' should appear in HTML")


class PaginationTemplateTestCase(TestCase):
    """
    Test partial template pagination.html
    """

    def setUp(self):
        self.template = 'snippets/pagination.html'

    def test_paginated_or_not(self):
        """
        If 'is_paginated' is in context, rendered html should contain "Search results pages"
        """
        content_if_paginated = 'Search results pages'

        paginator = Paginator(object_list=['a'], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=1)}
        rendered = render_to_string(self.template, context)
        self.assertTrue(
            content_if_paginated in rendered,
            "If 'is_paginated' is in context, rendered html should contain '{}'".format(content_if_paginated)
        )

        context = {'is_paginated': False,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=1)}
        rendered = render_to_string(self.template, context)
        self.assertFalse(
            content_if_paginated in rendered,
            "If 'is_paginated' not in context, rendered html shouldn't contain '{}'".format(content_if_paginated)
        )

    def test_page_obj_has_previous_or_not(self):
        """
        If there's a previous page, there should be a link to the previous page
        If there's no previous page, there should be a <span class="page-link">&laquo;</span>
        """

        disabled_previous_page = '<span class="page-link">&laquo;</span>'
        previous_page_js = 'onclick="return search_page.prev()'

        # If there's a previous page, there should be a link to the previous page
        paginator = Paginator(object_list=['a', 'b'], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=2)}
        rendered = render_to_string(self.template, context)
        self.assertTrue(previous_page_js in rendered,
                        "If there's a previous page, there should be a link to the previous page")
        self.assertFalse(disabled_previous_page in rendered,
                         "If there's a previous page, there should be no disabled 'previous page'")

        # If there's no previous page, there should be a disabled "previous page"
        paginator = Paginator(object_list=['a'], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=1)}
        rendered = render_to_string(self.template, context)
        self.assertTrue(disabled_previous_page in rendered,
                        "If there's no previous page, there should be a disabled 'previous page'")
        self.assertFalse(previous_page_js in rendered,
                         "If there's no previous page, there should be no link to a previous page")

    def test_page_obj_has_next_or_not(self):
        """
        If there's a next page, there should be a link to the next page, with search_text if it's in context:
            <a class="page-link" href="?page={{ page_obj.next_page_number }}
              {% if search_text %}&search_text={{ search_text }}{% endif %}">&raquo;</a>

        If there's no next page, there should be a <span class="page-link">&raquo;</span>
        """

        disabled_next_page = '<span class="page-link">&raquo;</span>'
        next_page_js = 'onclick="return search_page.next()'

        # If there's a next page, there should be a link to the next page
        paginator = Paginator(object_list=['a', 'b'], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=1)}
        rendered = render_to_string(self.template, context)
        self.assertTrue(next_page_js in rendered, "If there's a next page, there should be a link to the next page")
        self.assertFalse(disabled_next_page in rendered,
                         "If there's a next page, there should be no disabled 'next page'")

        # If there's no next page, there should be a disabled "next page"
        paginator = Paginator(object_list=['a'], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=1)}
        rendered = render_to_string(self.template, context)
        self.assertTrue(disabled_next_page in rendered,
                        "If there's no next page, there should be a disabled 'next page'")
        self.assertFalse(next_page_js in rendered,
                         "If there's no next page, there should be no link to a next page")

    def test_paginator_page_range(self):
        """
        The current page should be marked with <span class="visually-hidden-focusable">(current)</span>

        Otherwise for page numbers that are within 3 pages of the current page, there should be a link to them,
        with search text if it's in context
        """

        paginator = Paginator(object_list=['x' for i in range(15)], per_page=1)
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=8)}
        rendered = render_to_string(self.template, context)

        # Current page (8) should be marked "(current)" for screen reader
        current_page_span = '<span class="page-link">8 <span class="visually-hidden-focusable">(current)</span></span>'
        self.assertInHTML(current_page_span, rendered,
                          msg_prefix="Current page number should be marked with '(current)' for screen reader")

        # First 2 and last 2 page numbers (1-2 and 14-15),
        # and page numbers within 3 pages of current page (5-7 and 9-11) should have a link to them
        page_link = '''
        <a class="page-link" href="#" onclick="return letter_search.do_search({page_number});">{page_number}</a>'''
        for page_number in [1, 2, 5, 6, 7, 9, 10, 11, 14, 15]:
            self.assertInHTML(
                page_link.format(page_number=page_number), rendered,
                msg_prefix='1st and last 2, and page numbers within 3 pages of current page should have a link to them'
            )

        # Page numbers that are not the first 2 or last 2, or within 3 pages of current page should not have links
        context = {'is_paginated': True,
                   'paginator': paginator,
                   'page_obj': paginator.page(number=8)}
        rendered = render_to_string(self.template, context)
        partial_page_link = '<a class="page-link" href="#" onclick="return letter_search.do_search({page_number});"> '
        for page_number in [3, 4, 12, 13]:
            self.assertFalse(partial_page_link.format(page_number=page_number) in rendered,
                             "Page numbers not 1st or last 2, or within 3 pages of current page, shouldn't have a link")


class SearchListTemplateSnippetTestCase(TestCase):
    """
    Test search list template snippet
    """

    def test_template_content(self):
        template = 'snippets/search_list.html'
        letter = LetterFactory(date=ApproximateDate(1862, 1, 1),
                               writer=CorrespondentFactory(first_names='Francis P.', last_name='Black'),
                               recipient=CorrespondentFactory(first_names='Eveline', last_name='Johnston'),
                               place=PlaceFactory(name='Manassas Junction', state='Virginia'))
        Sentiment = namedtuple('Sentiment', ['id', 'name'])
        sentiments = [Sentiment(id=123, name='Positive/negative')]
        search_results = [(letter, 'sentiment highlight', sentiments, 'sentiment score')]

        rendered = render_to_string(template, context={'search_results': search_results})

        for heading in ['Date', 'Writer', 'Recipient', 'Place']:
            self.assertIn(heading, rendered, "Heading '{}' should appear in HTML".format(heading))
        self.assertIn(letter.list_date(), rendered, 'Letter list_date() should appear in HTML')
        self.assertIn(str(letter.writer), rendered, 'Letter writer should appear in HTML')
        self.assertIn(str(letter.recipient), rendered, 'Letter recipient should appear in HTML')
        self.assertIn(str(letter.place), rendered, 'Letter place should appear in HTML')
        self.assertIn('123', rendered, 'Sentiment ID should appear in HTML')
        self.assertIn('Positive/negative', rendered, 'Sentiment name should appear in HTML')
        self.assertIn('sentiment highlight', rendered, 'Sentiment highlight should appear in HTML')
        self.assertIn('sentiment score', rendered, 'Sentiment score should appear in HTML')


class SentimentDropdownTemplateSnippetTestCase(TestCase):
    """
    Test sentiment dropdown template snippet
    """

    def test_template_content(self):
        template = 'snippets/sentiment_dropdown.html'
        initial_filter_values = get_initial_filter_values()

        rendered = render_to_string(template, context={'filter_values': initial_filter_values})

        self.assertIn('Sentiments', rendered, "'Sentiments' should be in HTML")
        self.assertIn('123', rendered, 'Sentiment ID should be in HTML')
        self.assertIn('Positive/negative', rendered, 'Sentiment name should be in HTML')


class SentimentListTemplateSnippetTestCase(TestCase):
    """
    Test sentiment list template snippet
    """

    def test_template_content(self):
        template = 'snippets/sentiment_list.html'
        results = [('the sentiment', 'the highlighted text')]

        rendered = render_to_string(template, context={'results': results})

        self.assertIn('the sentiment', rendered, 'Sentiment should be in HTML')
        self.assertIn('the highlighted text', rendered, 'Highlighted text should be in HTML')


class SortByDropdownTemplateSnippetTestCase(TestCase):
    """
    Test sort by dropdown template snippet
    """

    def test_template_content(self):
        template = 'snippets/sort_by_dropdown.html'

        rendered = render_to_string(template, context={'sort_by': [(12, 'Date')]})

        self.assertIn('Sort by', rendered, "'Sort by' should be in HTML")
        self.assertIn('12', rendered, "sort_by ID should be in HTML")
        self.assertIn('Date', rendered, "sort_by name should be in HTML")


class StatsTableTemplateSnippetTestCase(TestCase):
    """
    Test stats table template snippet
    """

    def test_template_content(self):
        template = 'snippets/stats_table.html'
        words = ['oddment', 'tweak']
        month = 'April'
        freqs = ['freq1', 'freq2']
        proportion = 0.5
        average = 42
        total = 500
        num_letters = 23
        results = [(month, freqs, proportion, average, total, num_letters)]

        rendered = render_to_string(template, context={'words': words, 'results': results})

        for heading in ['Month', 'Avg. words per letter', 'Total words', 'Letters']:
            self.assertIn(heading, rendered, "'{}' heading should be in HTML".format(heading))
        for word in words:
            self.assertIn(word.capitalize(), rendered, "Capitalized word should be in HTML")
        self.assertIn(month, rendered, "Month should be in HTML")
        for freq in freqs:
            self.assertIn(freq, rendered, "Frequency should be in HTML")
        self.assertIn(str(average), rendered, "Average should be in HTML")
        self.assertIn(str(total), rendered, "Total should be in HTML")
        self.assertIn(str(num_letters), rendered, "Number of letters should be in HTML")

        # If show_proportion in context, proportion should be shown
        rendered = render_to_string(template, context={'words': words, 'results': results, 'show_proportion': True})
        self.assertIn(str(proportion), rendered, "Proportion should be in HTML if show_proportion in context")

        # If show_proportion not in context, proportion shouldn't be shown
        rendered = render_to_string(template, context={'words': words, 'results': results})
        self.assertNotIn(str(proportion), rendered, "Proportion shouldn't be in HTML if show_proportion not in context")
