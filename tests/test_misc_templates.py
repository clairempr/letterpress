from collections import namedtuple
from django_date_extensions.fields import ApproximateDate

from django.contrib.gis.geos import Point
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from letters.tests.factories import CorrespondentFactory, LetterFactory, PlaceFactory

# These are used in more than one place
FilterValues = namedtuple('FilterValues',
                          ['search_text', 'source_ids', 'writer_ids', 'start_date', 'end_date',
                           'words', 'sentiment_ids', 'sort_by'])
filter_values = FilterValues(
    search_text='This is the search text',
    source_ids=[1, 2, 3],
    writer_ids=[1, 2, 3],
    start_date='1863-01-01',
    end_date='1863-12-31',
    words=['oddment', 'tweak'],
    sentiment_ids=[1, 2, 3],
    sort_by='sort_by'
)
place = PlaceFactory(name='Manassas Junction', state='Virginia', point=Point(12.34, 56.78),
                     notes='https://en.wikipedia.org/wiki/Manassas,_Virginia')
letter = LetterFactory(date=ApproximateDate(1862, 1, 1),
                       writer=CorrespondentFactory(first_names='Francis P.', last_name='Black'),
                       recipient=CorrespondentFactory(first_names='Eveline', last_name='Johnston'),
                       heading='Januery the 1st / 62',
                       greeting='Miss Evey',
                       body='As this is the beginin of a new year I thought as I was a lone to night I would write you '
                            'a few lines to let you know that we are not all ded yet.',
                       closing='your friend as every',
                       signature='F.P. Black',
                       ps='p.s. remember me to all',
                       place=place)


class BaseTemplateTestCase(SimpleTestCase):
    """
    Test base template
    """

    def test_template_content(self):
        template = 'base.html'
        title = 'This is the title'
        rendered = render_to_string(template, context={'title': title})

        self.assertIn('<title>{}</title>'.format(title), rendered, "HTML should contain title")


class LetterTemplateTestCase(SimpleTestCase):
    """
    Test letter template
    """

    def test_template_content(self):
        template = 'letter.html'
        description = 'This is the description'

        rendered = render_to_string(template, context={'description': description, 'letter': letter})

        self.assertIn(description, rendered, "HTML should contain description")
        # Letter contents are in snippet letter_contents.html - just check the body here
        self.assertIn(letter.body, rendered, 'HTML should contain body')


class LetterSentimentTemplateTestCase(SimpleTestCase):
    """
    Test letter sentiment template
    """

    def test_template_content(self):
        template = 'letter_sentiment.html'
        description = 'This is the description'
        sentiment = 'This is the sentiment'
        results = {(sentiment, letter)}
        image = 'This is an image'

        rendered = render_to_string(template,
                                    context={'description': description, 'results': results, 'images': [image]})

        self.assertIn(sentiment, rendered, 'HTML should contain sentiment')
        # Letter contents are in snippet letter_contents.html - just check the body here
        self.assertIn(letter.body, rendered, 'HTML should contain body')


class LetterpressTemplateTestCase(SimpleTestCase):
    """
    Test letterpress template
    """

    def test_template_content(self):
        template = 'letterpress.html'
        image = 'copy-press.png'
        rendered = render_to_string(template)

        self.assertIn(image, rendered, 'HTML should contain image')
        self.assertIn('letterpress copying', rendered, "HTML should contain 'letterpress copying'")


class LettersTemplateTestCase(SimpleTestCase):
    """
    Test letters template
    """

    def test_template_content(self):
        template = 'letters.html'

        # Most of the page logic is in filter.html, so just spot-check here to see if it's used
        rendered = render_to_string(template, context={'filter_values': filter_values})
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(filter_values.start_date, rendered, "'Start date' should be in HTML")


class ObjNotFoundTemplateTestCase(SimpleTestCase):
    """
    Test obj not found template
    """

    def test_template_content(self):
        template = 'obj_not_found.html'
        object_id = 123
        object_type = 'Envelope'

        rendered = render_to_string(template, context={'object_id': object_id, 'object_type': object_type})

        self.assertTrue(rendered.count(object_type) == 2, 'Object type should appear twice in rendered HTML')
        self.assertIn(str(object_id), rendered, 'Object ID should appear in rendered HTML')


class PlaceTemplateTestCase(SimpleTestCase):
    """
    Test place template
    """

    def test_template_content(self):
        template = 'place.html'

        rendered = render_to_string(template, context={'place': place})

        self.assertIn(place.name, rendered, 'Place name should appear in rendered HTML')
        self.assertIn(place.state, rendered, 'Place state should appear in rendered HTML')
        self.assertIn(place.notes, rendered, 'Place notes, if filled, should appear in rendered HTML')
        # If place has coordinates, they should appear in HTML
        self.assertIn('Coordinates', rendered, "If place has coordinates, 'Coordinates' should appear in HTML")
        self.assertIn(str(place.point.x), rendered, "If place has coordinates, x-coordinate should appear in HTML")
        self.assertIn(str(place.point.y), rendered, "If place has coordinates, y-coordinate should appear in HTML")

        # If no letters in context, "Letters written here" shouldn't appear in HTML
        self.assertFalse('Letters written here' in rendered,
                         "If no letters in context, 'Letters written here' shouldn't appear in HTML")

        rendered = render_to_string(template, context={'place': place, 'letters': [letter]})

        # If letters in context, "Letters written here" should appear in HTML
        self.assertIn('Letters written here', rendered,
                      "If letters in context, 'Letters written here' should appear in HTML")
        self.assertIn(letter.list_date(), rendered,
                      "If letters in context, letter list_date should appear in HTML")
        self.assertIn(str(letter.writer), rendered,
                      "If letters in context, letter writer should appear in HTML")
        self.assertIn(str(letter.recipient), rendered,
                      "If letters in context, letter recipient should appear in HTML")


class PlacesTemplateTestCase(SimpleTestCase):
    """
    Test places template
    """

    def test_template_content(self):
        template = 'places.html'

        # Most of the page logic is in filter.html, so just spot-check here to see if it's used
        rendered = render_to_string(template, context={'filter_values': filter_values})
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(filter_values.start_date, rendered, "'Start date' should be in HTML")


class SentimentTemplateTestCase(SimpleTestCase):
    """
    Test sentiment template
    """

    def test_template_content(self):
        template = 'sentiment.html'

        # Most of the page logic is in filter.html, so just spot-check here to see if it's used
        rendered = render_to_string(template, context={'filter_values': filter_values})
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(filter_values.start_date, rendered, "'Start date' should be in HTML")


class StatsTemplateTestCase(SimpleTestCase):
    """
    Test stats template
    """

    def test_template_content(self):
        template = 'stats.html'
        chart = 'This is the chart'
        stats = 'These are the stats'

        rendered = render_to_string(template, context={'filter_values': filter_values, 'chart': chart, 'stats': stats})

        self.assertIn(chart, rendered, "Chart should be in HTML")
        self.assertIn(stats, rendered, "Stats should be in HTML")

        # Some of the page logic is in filter.html, so just spot-check here to see if it's used
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(filter_values.start_date, rendered, "'Start date' should be in HTML")


class TextSentimentTemplateTestCase(SimpleTestCase):
    """
    Test text sentiment template
    """

    def test_template_content(self):
        template = 'text_sentiment.html'

        Sentiment = namedtuple('Sentiment', ['id', 'name'])
        sentiments = [Sentiment(id=0, name='Positive/negative')]
        initial_filter_values = {
            'sources': [],
            'writers': [],
            'start_date': '1863-01-01',
            'end_date': '1863-12-31',
            'words': ['oddment', 'tweak'],
            'sentiments': sentiments
        }

        rendered = render_to_string(template, context={'filter_values': initial_filter_values})

        self.assertIn('Text to analyze', rendered, "'Text to analyze' should be in HTML")

        # Some of the page logic is in sentiment_dropdown.html, so just spot-check here to see if it's used
        self.assertIn('Positive/negative', rendered, "'Positive/negative' should be in HTML")


class WordCloudTemplateTestCase(SimpleTestCase):
    """
    Test word cloud template
    """

    def test_template_content(self):
        template = 'wordcloud.html'
        wordcloud = 'This is the wordcloud'

        rendered = render_to_string(template, context={'filter_values': filter_values, 'wordcloud': wordcloud})

        self.assertIn('<img id="wordcloud"', rendered, "WordCloud image placeholder should be in HTML")

        # Some of the page logic is in filter.html, so just spot-check here to see if it's used
        self.assertIn('Start date', rendered, "'Start date' should be in HTML")
        self.assertIn(filter_values.start_date, rendered, "'Start date' should be in HTML")
