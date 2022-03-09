import bokeh

from bokeh.models import LayoutDOM
from pandas import DataFrame

from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.html import format_html

from letters.charts import get_frequency_charts, get_per_month_chart, get_proportions_chart, make_charts


class GetFrequencyChartsTestCase(SimpleTestCase):
    """
    get_frequency_charts() should return a time series bar chart
    """

    @patch('letters.charts.str')
    def test_get_frequency_charts(self, mock_str):
        words = ['&', 'and']
        frequency_df = DataFrame()
        frequency_df['&'] = [12, 17, 1, 16]
        frequency_df['and'] = [1, 1, 0, 0]
        frequency_df['Month'] = ['1863-01', '1863-02', '1863-03', '1863-04']

        mock_str.format.return_value = 'formatted string'

        # Test that TimeSeries and Bar get created without error
        get_frequency_charts(words, frequency_df)
        mock_str.reset_mock()

        # get_frequency_charts() should call str.format() if only one word given
        with patch('letters.charts.TimeSeries', autospec=True) as mock_TimeSeries:
            with patch('letters.charts.Bar', autospec=True) as mock_Bar:
                with patch('pandas.melt', autospec=True) as mock_melt:

                    # mock_TimeSeries.return_value = 'time_series'
                    mock_TimeSeries.return_value = 'line'
                    mock_Bar.return_value = 'bar'
                    mock_melt.return_value = frequency_df

                    words = ['and']

                    get_frequency_charts(words, frequency_df)

                    self.assertEqual(mock_str.format.call_count, 1,
                                     'get_frequency_charts() should call str.format() if no words given')
                    mock_Bar.reset_mock()
                    mock_melt.reset_mock()

                    # More than one word given
                    words = ['and', '&']
                    result = get_frequency_charts(words, frequency_df)

                    # get_frequency_charts() should call/create a Bokeh TimeSeries with words as kwarg 'y'
                    args, kwargs = mock_TimeSeries.call_args
                    self.assertEqual(kwargs['y'], words,
                                     "get_frequency_charts() should call/create Bokeh TimeSeries with words as kwarg 'y'")

                    # get_frequency_charts() should call pandas melt()
                    self.assertEqual(mock_melt.call_count, 1, 'get_frequency_charts() should call pandas melt()')

                    # get_frequency_charts() should call/create a Bokeh Bar
                    self.assertEqual(mock_Bar.call_count, 1, 'get_frequency_charts() should call/create Bokeh Bar')

                    # get_frequency_charts() should return [return value of Bar, return value of Timeseries]
                    self.assertEqual(result, [mock_Bar.return_value, mock_TimeSeries.return_value],
                                              'get_frequency_charts() should return [return val of Bar, return val of Timeseries]')


class GetPerMonthChartTestCase(SimpleTestCase):
        """
        get_per_month_chart() should return a Bokeh TimeSeries of
        whatever is in the pandas DataFrame, per month
        """

        def test_get_per_month_chart(self):
            df = DataFrame({'Month': ['1863-01', '1863-02', '1863-03', '1863-04']})
            df['something_per_month'] = [2, 2, 3, 3]

            title = 'Title'
            label = 'TPS Reports Per Month'

            # First test the real thing to make sure there's not an error
            get_per_month_chart(df, title, label)

            # Now mock TimeSeries and see if it's called with the right args,
            # and if get_per_month_chart() returns it
            with patch('letters.charts.TimeSeries', autospec=True) as mock_TimeSeries:
                mock_TimeSeries.return_value = 'timeseries'

                result = get_per_month_chart(df, title, label)
                args, kwargs = mock_TimeSeries.call_args
                self.assertEqual(set(args[0]), set(df),
                                 'get_per_month_chart() should create a TimeSeries with DataFrame as 1st arg')
                self.assertEqual(kwargs['title'], title,
                                 'get_per_month_chart() should create a TimeSeries with title as kwarg')
                self.assertEqual(kwargs['ylabel'], label,
                                 'get_per_month_chart() should create a TimeSeries with label as kwarg')
                self.assertEqual(result, mock_TimeSeries.return_value,
                                 'get_per_month_chart() should return a Bokeh TimeSeries')


class GetProportionsChartTestCase(SimpleTestCase):
    """
    get_proportions_chart() should create a time series of the
    proportions of the use of one word compared to another
    """

    def test_get_proportions_chart(self,):
        words = ['and', '&']
        months = ['1863-01', '1863-02', '1863-03', '1863-04']
        proportions = [3.19672131147541, 1.6153846153846154, 4.607843137254902, 1.6388888888888888]
        df = DataFrame({'Month': months, 'Proportion': proportions})

        # Test that TimeSeries gets created without error
        get_proportions_chart(words, df)

        # Test that get_proportions_chart() returns the Bokeh TimeSeries that was created
        with patch('letters.charts.TimeSeries', autospec=True) as mock_TimeSeries:
            mock_TimeSeries.return_value = 'proportions chart'

            result = get_proportions_chart(words, df)
            self.assertEqual(result, mock_TimeSeries.return_value)


class MakeChartsTestCase(SimpleTestCase):
    """
    make_charts() should create Bokeh charts for word frequencies and totals over time
    and return some rendered html
    """

    @patch('letters.charts.get_frequency_charts', autospec=True)
    @patch('letters.charts.get_proportions_chart', autospec=True)
    @patch('letters.charts.get_per_month_chart', autospec=True)
    @patch('letters.charts.render_to_string', autospec=True)
    def test_make_charts(self, mock_render_to_string, mock_get_per_month_chart, mock_get_proportions_chart,
                         mock_get_frequency_charts):

        # Bokeh row() expects a LayoutDOM object, so just create an empty one for the mock to use
        mock_get_per_month_chart.return_value = LayoutDOM()
        mock_render_to_string.return_value = 'stuff that got returned'

        words = ['word',]
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
        self.assertEqual(args[0], words,
            'make_charts() should call get_proportions_chart() with words as 1st arg if # of words searched for == 2')

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
