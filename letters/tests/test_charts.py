import bokeh

from bokeh.models import LayoutDOM
from bokeh.plotting import Figure

from unittest.mock import patch

from django.test import SimpleTestCase

from letters.charts import get_bokeh_figure, get_frequency_charts, get_per_month_chart, get_proportions_chart, \
    make_charts


class GetFrequencyChartsTestCase(SimpleTestCase):
    """
    get_frequency_charts() should return a time series bar chart
    """

    @patch('letters.charts.str')
    def test_get_frequency_charts(self, mock_str):
        mock_str.format.return_value = 'formatted string'

        words = ['&', 'and']
        months = ['1863-01', '1863-02', '1863-03', '1863-04']
        word_freqs = [[12, 17, 1, 16], [1, 1, 0, 0]]

        # Test that TimeSeries and Bar get created without error
        get_frequency_charts(words, months, word_freqs)
        mock_str.reset_mock()

        # get_frequency_charts() should call str.format() if only one word given
        with patch.object(bokeh.plotting, 'figure') as mock_figure:
            mock_figure.return_value = 'figure'

            words = ['and']

            get_frequency_charts(words, months, [[12, 17, 1, 16]])

            self.assertEqual(mock_str.format.call_count, 1,
                             'get_frequency_charts() should call str.format() if no words given')
            # More than one word given
            words = ['and', '&']
            result = get_frequency_charts(words, months, word_freqs)

            # get_frequency_charts() should return [return value of Bar, return value of Figure]
            self.assertEqual(type(result[0]), Figure,
                             'get_per_month_chart() should return a Bokeh Figure as 1st result')
            self.assertEqual(type(result[1]), Figure,
                             'get_per_month_chart() should return a Bokeh Figure as 2nd result')


class GetPerMonthChartTestCase(SimpleTestCase):
    """
    get_per_month_chart() should return a Bokeh Figure of values, per month
    """

    def test_get_per_month_chart(self):
        months = ['1863-01', '1863-02', '1863-03', '1863-04']
        values = [2, 2, 3, 3]
        title = 'Title'
        label = 'TPS Reports Per Month'

        # First test the real thing to make sure there's not an error
        get_per_month_chart(months, values, title, label)

        # Now mock figure.line() and see if it's called with the right args,
        with patch.object(bokeh.plotting.Figure, 'line', autospec=True) as mock_figure_line:
            mock_figure_line.return_value = 'figure line'

            get_per_month_chart(months, values, title, label)

            args, kwargs = mock_figure_line.call_args
            self.assertEqual(args[1], months,
                             'get_per_month_chart() should create a line with months as 2nd arg')
            self.assertEqual(args[2], values,
                             'get_per_month_chart() should create a line with values as 3rd arg')
            self.assertIn('line_color', kwargs,
                          'get_per_month_chart() should create a line with line_color in kwargs')
            self.assertIn('line_width', kwargs,
                          'get_per_month_chart() should create a line with line_width in kwargs')

        # get_per_month_chart() should return a Bokeh Figure
        with patch.object(bokeh.plotting, 'figure'):
            result = get_per_month_chart(months, values, title, label)
            self.assertEqual(type(result), Figure, 'get_per_month_chart() should return a Bokeh Figure')


class GetProportionsChartTestCase(SimpleTestCase):
    """
    get_proportions_chart() should create a time series of the
    proportions of the use of one word compared to another
    """

    def test_get_proportions_chart(self):
        words = ['and', '&']
        months = ['1863-01', '1863-02', '1863-03', '1863-04']
        proportions = [3.19672131147541, 1.6153846153846154, 4.607843137254902, 1.6388888888888888]

        # Test that TimeSeries gets created without error
        get_proportions_chart(words, months, proportions)

        # get_proportions_chart() should return a Bokeh Figure
        with patch.object(bokeh.plotting, 'figure'):
            result = get_proportions_chart(words, months, proportions)
            self.assertEqual(type(result), Figure, 'get_proportions_chart() should return a Bokeh Figure')


class MakeChartsTestCase(SimpleTestCase):
    """
    make_charts() should create Bokeh charts for word frequencies and totals over time
    and return some rendered html
    """

    @patch('letters.charts.get_frequency_charts', autospec=True)
    @patch('letters.charts.get_proportions_chart', autospec=True)
    @patch('letters.charts.get_per_month_chart', autospec=True)
    @patch('bokeh.layouts.Row', autospec=True)
    @patch('letters.charts.render_to_string', autospec=True)
    def test_make_charts(self, mock_render_to_string, mock_row, mock_get_per_month_chart, mock_get_proportions_chart,
                         mock_get_frequency_charts):
        # Bokeh row() expects a LayoutDOM object, so just create empty ones for the mocks to use
        mock_get_per_month_chart.return_value = LayoutDOM()
        mock_get_proportions_chart.return_value = LayoutDOM()
        # There are two frequency charts
        mock_get_frequency_charts.return_value = [LayoutDOM(), LayoutDOM()]
        mock_row.return_value = LayoutDOM()
        mock_render_to_string.return_value = 'stuff that got returned'

        words = ['word', ]
        months = ['Jan']
        proportions = [1]
        word_freqs = [1]
        totals = [1]
        averages = [1]
        doc_counts = [1]

        make_charts(words=words, months=months, proportions=proportions, word_freqs=word_freqs, totals=totals,
                    averages=averages, doc_counts=doc_counts)
        mock_get_per_month_chart.reset_mock()

        args, kwargs = mock_get_frequency_charts.call_args
        self.assertEqual(args[0], words, 'make_charts() should call get_frequency_charts() with words as 1st arg')

        # If number of words searched for is not 2, get_proportions_chart() shouldn't be called
        self.assertEqual(mock_get_proportions_chart.call_count, 0,
                         "make_charts() shouldn't call get_proportions_chart() if # of words searched for != 2")

        # If number of words searched for is 2, get_proportions_chart() should be called
        words = ['and', '&']
        months = [1, 2]
        proportions = [1, 2]
        word_freqs = [1, 2, 3, 4]
        totals = [1, 2]
        averages = [1, 2]
        doc_counts = [1, 2]

        result = make_charts(words=words, months=months, proportions=proportions, word_freqs=word_freqs, totals=totals,
                             averages=averages, doc_counts=doc_counts)
        args, kwargs = mock_get_frequency_charts.call_args
        self.assertEqual(
            args[0], words,
            'make_charts() should call get_proportions_chart() with words as 1st arg if # of words searched for == 2'
        )

        # get_per_month_chart() should be called 3 times
        self.assertEqual(mock_get_per_month_chart.call_count, 3,
                         'make_charts() should call get_per_month_chart() 3 times')

        # render_to_string() should be called and its return value returned
        args, kwars = mock_render_to_string.call_args
        self.assertEqual(args[0], 'snippets/chart.html',
                         'make_charts() should call render_to_string() with charts snippet as first arg')
        for key in ['script', 'divs']:
            self.assertTrue(key in args[1],
                            "make_charts() should call render_to_string() with '{}' in second arg")

        # make_charts() should return the return value of render_to_string
        self.assertEqual(result, mock_render_to_string.return_value,
                         'make_charts() should return the return value of render_to_string')


class GetBokehFigureTestCase(SimpleTestCase):
    """
    get_bokeh_figure() should return a Bokeh figure
    """

    @patch.object(bokeh.plotting, 'figure', autospec=True)
    def test_get_bokeh_figure(self, mock_figure):
        months = ['1863-01', '1863-02', '1863-03', '1863-04']
        title = 'Doohickeys per month'

        result = get_bokeh_figure(months, title)
        self.assertEqual(type(result), Figure, 'get_bokeh_figure() should return a Bokeh figure')
