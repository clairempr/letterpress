from bokeh.embed import components
from bokeh.charts import Bar, TimeSeries
import pandas as pd
from django.template.loader import render_to_string


def make_charts(words, months, proportions, word_freqs, totals, averages, doc_counts):
    charts = []

    # Make proportions chart if 2 words were searched for
    if len(words) == 2:
        chart = get_proportions_chart(words, months, proportions)
        charts.append(components(chart))

    # Freqency chart
    chart = get_frequency_chart(words, months, word_freqs)
    charts.append(components(chart))

    # Totals chart
    chart = get_per_month_chart(months, totals, 'Total words')
    charts.append(components(chart))

    # Averages chart
    chart = get_per_month_chart(months, averages, 'Average words')
    charts.append(components(chart))

    # Number of letters chart
    chart = get_per_month_chart(months, doc_counts, 'Letters')
    charts.append(components(chart))

    # Feed them to the Django template.
    return render_to_string('snippets/chart.html',
                              {'charts': charts})


def get_frequency_chart(words, months, word_freqs):
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
    bar = Bar(data, values='frequency', label='month', stack='word',
              title=title, legend='top_right',
              color=['blue', 'grey'])
    return bar


def get_proportions_chart(words, months, proportions):
    title = str.format('Proportions of "{0}" to "{1}"', words[0], words[1])
    s = pd.Series(proportions, index=months)
    time_series = TimeSeries(s, title=title, xlabel='Month', ylabel='Proportion', legend=False, color='blue')
    return time_series


def get_per_month_chart(months, values, label):
    title = str.format('{0} per month', label)
    s = pd.Series(values, index=months)
    time_series = TimeSeries(s, title=title, xlabel='Month', ylabel=label, legend=False, color='blue')
    return time_series


