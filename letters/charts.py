from bokeh.embed import components
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

    # word_freqs are in the format [freq_word1_month1, freq_word2_month1 freq_word1_month2, freq_word2_month2,...]
    # and they need to be in format {month1: [freq_word1, freq_word2], month2: [freq_word1, freq_word2], ...}
    word_freqs_by_word = []
    for idx, _ in enumerate(words):
        word_freqs_by_word.extend([word_freqs[idx::len(words)]])

    fcharts = get_frequency_charts(words, months, word_freqs_by_word)

    # Make proportions chart if 2 words were searched for
    if len(words) == 2:
        proportions_chart = get_proportions_chart(words, months, proportions)
        fcharts.append(proportions_chart)

    # Totals chart
    totals_chart = get_per_month_chart(months, totals,
                                       'Total words per month', 'Total words')
    # Averages chart
    averages_chart = get_per_month_chart(months, averages,
                                         'Average words per letter', 'Average words')
    # Number of letters chart
    doc_count_chart = get_per_month_chart(months, doc_counts,
                                          'Letters per month', 'Letters')

    charts.append(row(fcharts, sizing_mode='scale_width'))
    charts.append(row(totals_chart, doc_count_chart, averages_chart, sizing_mode='scale_width'))

    script, divs = components(charts)

    # Feed them to the Django template.
    return render_to_string('snippets/chart.html',
                              {'script': script, 'divs': divs})


def get_frequency_charts(words, months, word_freqs):
    """
    Return a time series bar chart
    """

    title = 'Frequency of '
    for idx, word in enumerate(words):
        if idx > 0:
            title += ' and '
        title += str.format('"{0}"', word)

    line_chart = get_bokeh_figure(months, title)
    line_chart.xaxis.axis_label = 'Month'
    line_chart.xaxis.major_label_orientation = 0.8
    line_chart.yaxis.axis_label = 'Frequency'
    line_chart.legend.location = 'top_right'

    for idx, freqs in enumerate(word_freqs):
        line_chart.line(x=months, y=freqs, color=PALETTE[idx], line_width=1.75, legend=words[idx])

    bar_chart = get_bokeh_figure(months, title)
    bar_chart.xaxis.axis_label = 'Month'
    bar_chart.xaxis.major_label_orientation = 0.8
    bar_chart.yaxis.axis_label = 'Frequency'
    bar_chart.legend.location = 'top_right'

    for idx, freqs in enumerate(word_freqs):
        bar_chart.vbar(x=months, top=freqs, width=0.5, bottom=0, line_dash_offset=1, color=PALETTE[idx],
                       legend=words[idx])

    return [bar_chart, line_chart]


def get_proportions_chart(words, months, proportions):
    """
    Create a time series of the proportions of the use of one word compared to another
    """

    title = str.format('Proportions of "{0}" to "{1}"', words[0], words[1])
    chart = get_bokeh_figure(months, title)
    chart.xaxis.axis_label = 'Month'
    chart.xaxis.major_label_orientation = 0.8
    chart.yaxis.axis_label = 'Proportion'
    chart.line(months, proportions, line_color=PALETTE[0], line_width=1.75)

    return chart


def get_per_month_chart(months, values, title, label):
    chart = get_bokeh_figure(months, title)
    chart.xaxis.axis_label = 'Month'
    chart.xaxis.major_label_orientation = 0.8
    chart.yaxis.axis_label = label
    # Can't refer to 2nd column by name because it's variable
    chart.line(months, values, line_color=PALETTE[0], line_width=1.75)

    return chart


def get_bokeh_figure(months, title):
    chart = figure(plot_width=400, plot_height=400, x_range=list(months),
                   title=title, y_axis_type='linear', toolbar_location='right')
    return chart
