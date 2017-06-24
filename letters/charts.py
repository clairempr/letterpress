from bokeh.embed import components
from bokeh.charts import Bar, TimeSeries
from bokeh.layouts import row
from django.template.loader import render_to_string
import pandas as pd

# Colors for Bokeh palette
# royal blue: #4582ec
# light blue: #aed5f9
# gray: #a6a6a6
# medium turquoise: #5bc0de
# cornflower blue: #6699ef

PALETTE = ['#4582ec', '#a6a6a6', '#aed5f9', '#5bc0de', '#6699ef']


def make_charts(words, months, proportions, word_freqs, totals, averages, doc_counts):
    charts = []

    # Freqency chart
    fcharts = get_frequency_charts(words, months, word_freqs)

    # Make proportions chart if 2 words were searched for
    if len(words) == 2:
        proportions_chart = get_proportions_chart(words, months, proportions)
        fcharts.append(proportions_chart)

    # Totals chart
    totals_chart = get_per_month_chart(months, totals, 'Total words per month', 'Total words')

    # Averages chart
    averages_chart = get_per_month_chart(months, averages, 'Average words per letter', 'Average words')

    # Number of letters chart
    doc_count_chart = get_per_month_chart(months, doc_counts, 'Letters per month', 'Letters')

    charts.append(row(children=fcharts, responsive=True))
    charts.append(row(totals_chart, doc_count_chart, averages_chart, responsive=True))

    script, divs = components(charts)

    # Feed them to the Django template.
    return render_to_string('snippets/chart.html',
                              {'script': script, 'divs': divs})


def get_frequency_charts(words, months, word_freqs):
    title = 'Frequency of '
    for idx, word in enumerate(words):
        if idx > 0:
            title += ' and '
        title += str.format('"{0}"', word)

    # best support for bar chart is with data in a format that is table-like
    bar_words = []
    bar_months = []
    for month in months:
        bar_words.extend(words)
        for i in range(len(words)):
            bar_months.append(month)

    data = {
        'word': bar_words,
        'month': bar_months,
        'frequency': word_freqs
    }

    # x-axis labels pulled from the months column, stacking labels from words column
    bar = Bar(data, values='frequency', label='month', group='word',#stack='word',
              title=title, legend='top_right', bar_width=1,
              palette=PALETTE, toolbar_location='right')

    data = {
        'month': months,
    }
    for idx, word in enumerate(words):
        data[word] = word_freqs[idx::len(words)]

    time_series = TimeSeries(data, title=title, x='month', y=words, xlabel='Month', ylabel='Frequency',
                             legend='top_right', palette=PALETTE, toolbar_location='right')
    return [bar, time_series]


def get_proportions_chart(words, months, proportions):
    title = str.format('Proportions of "{0}" to "{1}"', words[0], words[1])
    s = pd.Series(proportions, index=months)
    time_series = TimeSeries(s, title=title, xlabel='Month', ylabel='Proportion', legend=False,
                             palette=PALETTE, toolbar_location='right')
    return time_series


def get_per_month_chart(months, values, title, label):
    s = pd.Series(values, index=months)
    time_series = TimeSeries(s, title=title, xlabel='Month', ylabel=label, legend=False,
                             palette=PALETTE, toolbar_location='right')
    return time_series


