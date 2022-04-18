import pandas as pd

from bokeh.embed import components
from bokeh.charts import Bar, TimeSeries
from bokeh.layouts import row
from bokeh.plotting import figure

from django.template.loader import render_to_string

# Colors for Bokeh palette
# royal blue: #4582ec
# light blue: #aed5f9
# gray: #a6a6a6
# medium turquoise: #5bc0de
# cornflower blue: #6699ef

PALETTE = ['#4582ec', '#a6a6a6', '#aed5f9', '#5bc0de', '#6699ef']


def make_charts(words, months, proportions, word_freqs, totals, averages, doc_counts):
    """
    Create Bokeh charts for word frequencies and totals over time
    and return some rendered html
    """

    charts = []

    # Make pandas dataframe with word frequencies
    # word_freqs is a list of word frequencies, grouped by month and then by word
    frequency_df = pd.DataFrame()
    # Every n elements is for word
    for idx, word in enumerate(words):
        frequency_df[word] = word_freqs[idx::len(words)]
    frequency_df['Month'] = months

    fcharts = get_frequency_charts(words, frequency_df)

    # Make proportions chart if 2 words were searched for
    if len(words) == 2:
        proportions_df = pd.DataFrame({'Month': months, 'Proportion': proportions})
        proportions_chart = get_proportions_chart(words, proportions_df)
        fcharts.append(proportions_chart)

    # Totals chart
    totals_chart = get_per_month_chart(pd.DataFrame({'Month': months, 'Total': totals}),
                                               'Total words per month', 'Total words')
    # Averages chart
    averages_chart = get_per_month_chart(pd.DataFrame({'Month': months, 'Average': averages}),
                                                 'Average words per letter', 'Average words')
    # Number of letters chart
    doc_count_chart = get_per_month_chart(pd.DataFrame({'Month': months, 'Average': doc_counts}),
                                                  'Letters per month', 'Letters')

    charts.append(row(children=fcharts, responsive=True))
    charts.append(row(totals_chart, doc_count_chart, averages_chart, responsive=True))

    script, divs = components(charts)

    # Feed them to the Django template.
    return render_to_string('snippets/chart.html',
                              {'script': script, 'divs': divs})


def get_frequency_charts(words, df):
    """
    Return a time series bar chart
    """

    title = 'Frequency of '
    for idx, word in enumerate(words):
        if idx > 0:
            title += ' and '
        title += str.format('"{0}"', word)

    time_series = TimeSeries(df, title=title, y=words,
                             x='Month',
                             xlabel='Month', ylabel='Frequency',
                             legend='top_right',
                             palette=PALETTE, toolbar_location='right')

    df = pd.melt(df, id_vars='Month').dropna().set_index('Month')
    bar = Bar(df, values='value', group='variable', label='Month',
              ylabel='Frequency',
              title=title, legend='top_right', bar_width=1,
              palette=PALETTE, toolbar_location='right')

    return [bar, time_series]


def get_proportions_chart(words, df):
    """
    Create a time series of the proportions of the use of one word compared to another
    """

    title = str.format('Proportions of "{0}" to "{1}"', words[0], words[1])
    time_series = TimeSeries(df, title=title, x='Month',
                             xlabel='Month', ylabel='Proportion', legend=False,
                             palette=PALETTE, toolbar_location='right')
    return time_series


def get_per_month_chart(df, title, label):
    chart = figure(plot_width=400, plot_height=400, x_range=list(df.Month),
                   title=title, y_axis_type='linear', toolbar_location='right')
    chart.xaxis.axis_label = df.columns[0]
    chart.xaxis.major_label_orientation = 0.8
    chart.yaxis.axis_label = df.columns[1]
    chart.yaxis.axis_label = label
    chart.line(df.Month, df.iloc[:, 1], line_color=PALETTE[0], line_width=1.75)

    return chart
