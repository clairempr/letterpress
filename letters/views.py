import csv
import json
import random
from copy import deepcopy

# for wordcloud, csv
from io import BytesIO, StringIO
import base64
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from os import path
from letterpress import settings
from PIL import Image
from wordcloud import WordCloud, STOPWORDS

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import mark_safe
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from letterpress.exceptions import ElasticsearchException
from letter_sentiment.custom_sentiment import get_custom_sentiment_for_text, highlight_for_custom_sentiment
from letter_sentiment.sentiment import get_sentiment, highlight_text_for_sentiment

from letters import letter_search
from letters import filter as letters_filter
from letters.charts import make_charts
from letters.mixins import ObjectNotFoundMixin, object_not_found
from letters.models import Letter, Place
from letters.sort_by import DATE, RELEVANCE, get_sentiments_for_sort_by_list


class LettersView(TemplateView):
    """
    Show page for searching for letters, with filters
    """

    template_name = 'letters.html'

    def post(self, request, *args, **kwargs):
        # for export, return all matching records, within reason
        size = 10000

        try:
            es_result = letter_search.do_letter_search(request, size, page_number=0)
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        letters = [letter for letter, highlight, sentiment, score in es_result.search_results]
        if request.POST.get('export_text'):
            return export_text(letters)
        else:
            return export_csv(letters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Letters'
        context['nbar'] = 'letters_view'
        context['filter_values'] = letters_filter.get_initial_filter_values()
        context['show_search_text'] = 'true'
        context['sort_by'] = [(DATE, 'Date'), (RELEVANCE, 'Relevance')]
        context['show_export_button'] = 'true'

        return context


class StatsView(TemplateView):
    """
    Show page for requesting various stats about word use over time
    """

    template_name = 'stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Letter statistics'
        context['nbar'] = 'stats'
        context['filter_values'] = letters_filter.get_initial_filter_values()
        context['show_words'] = 'true'

        return context


class GetStatsView(View):
    """
    Retrieve stats for requested words/months, based on filter
    """

    def post(self, request, *args, **kwargs):
        filter_values = letters_filter.get_filter_values_from_request(request)

        try:
            es_word_counts = letter_search.get_word_counts_per_month(filter_values)
            words = filter_values.words
            if words:
                es_word_freqs = letter_search.get_multiple_word_frequencies(filter_values)
            else:
                es_word_freqs = []
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        if len(words) == 2:
            show_proportion = 'true'
        else:
            show_proportion = ''

        months = sorted(list(es_word_counts.keys()))
        results = []

        proportions = []
        chart_word_freqs = []
        chart_totals = [es_word_counts[month]['total_words'] for month in months]
        chart_averages = [es_word_counts[month]['avg_words'] for month in months]
        chart_doc_counts = [es_word_counts[month]['doc_count'] for month in months]
        show_charts = False

        for month in months:
            proportion = 0
            total = 0
            freqs = []

            for word in words:
                if month in es_word_freqs:
                    freq = es_word_freqs[month][word]
                    show_charts = True
                else:
                    freq = 0
                total += freq
                freqs.append(freq)

            if show_proportion and (total - freqs[0] != 0):
                proportion = freqs[0] / (total - freqs[0])

            results.append((month, freqs, proportion,
                            es_word_counts[month]['avg_words'],
                            es_word_counts[month]['total_words'],
                            es_word_counts[month]['doc_count']))

            proportions.append(proportion)
            chart_word_freqs.extend(freqs)

        stats_html = render_to_string('snippets/stats_table.html', {'words': words, 'show_proportion': show_proportion, 'results': results})
        if show_charts:
            chart = make_charts(words, months, proportions, chart_word_freqs, chart_totals, chart_averages, chart_doc_counts)
        else:
            chart = ''

        # This was Ajax
        return HttpResponse(json.dumps({'stats': stats_html, 'chart': chart}), content_type="application/json")


class WordCloudView(TemplateView):
    """
    Show page for generating word clouds
    """

    template_name = 'wordcloud.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Word cloud'
        context['nbar'] = 'stats'
        context['filter_values'] = letters_filter.get_initial_filter_values()
        context['show_search_text'] = 'true'

        return context


class GetWordCloudView(View):
    """
    Return WordCloud image, based on filter
    """

    def get(self, request, *args, **kwargs):
        # return all matching records, within reason
        try:
            es_result = letter_search.do_letter_search(request, size=10000, page_number=0)
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        letters = [letter for letter, highlight, sentiment, score in es_result.search_results]
        text = ' '.join([letter.contents() for letter in letters])
        if text.rstrip() == '':
            return HttpResponse(json.dumps({'wc': ''}), content_type="application/json")

        stopwords = set(STOPWORDS)

        mask = None
        with Image.open(path.join(settings.STATIC_ROOT, 'images/parchment_horiz.png')) as shape_file:
            mask = np.array(shape_file)
            # mask = np.array(Image.open(path.join(settings.STATIC_ROOT, 'images/envelope.png')))

        cmap = LinearSegmentedColormap.from_list(name='letterpress_colormap',
                                                 colors=['#a1bdef', '#7da5ef', '#5c90ef'],
                                                 N=10)
        wc = WordCloud(max_words=1000, mask=mask, stopwords=stopwords, margin=2,
                       background_color='black', colormap=cmap, scale=0.95)\
            .generate(text)

        # Save generated image as base64 and convert to string so it can
        # be returned as json and used in the Ajax success function
        # Just returning an image response doesn't force the browser to
        # show the updated image, even with the @never_cache decorator
        wc_image = wc.to_image()

        with BytesIO() as byteImgIO:
            wc_image.save(byteImgIO, 'PNG')
            byteImgIO.seek(0)
            wc_image = base64.b64encode(byteImgIO.read())

        # decode bytes to text
        wc_string = wc_image.decode('utf-8')
        json_data = json.dumps({'wc': wc_string}, indent=2)

        # This was Ajax
        return HttpResponse(json_data, content_type="application/json")


class SentimentView(TemplateView):
    """
    Show page for viewing sentiment of letters
    """

    template_name = 'sentiment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sort_by = [(DATE, 'Date')]
        sort_by.extend(get_sentiments_for_sort_by_list())

        context['title'] = 'Letter sentiment'
        context['nbar'] = 'sentiment'
        context['filter_values'] = letters_filter.get_initial_filter_values()
        context['show_search_text'] = 'true'
        context['sort_by'] = sort_by
        context['show_sentiment'] = 'true'

        return context


class LetterSentimentView(View):
    """
    View to show one letter by id, with highlights for selected sentiment
    """

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('letter_id')
        try:
            letter = Letter.objects.get(pk=pk)
        except Letter.DoesNotExist:
            return object_not_found(self.request, pk, 'Letter')

        # sentiments is a list of tuples (id, value)
        sentiments = letter_search.get_letter_sentiments(letter, self.kwargs.get('sentiment_id'))

        try:
            return get_highlighted_letter_sentiment(request, letter, sentiments=sentiments)
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=False)


def get_highlighted_letter_sentiment(request, letter, sentiments):
    """
    Show particular letter with sentiment highlights
    """

    highlighted_letters = []
    sentiment_values = []

    for sentiment in sentiments:
        sentiment_id, value = sentiment
        highlighted_letter = highlight_letter_for_sentiment(letter, sentiment_id)

        # Sentiment value might be a list
        if isinstance(value, str):
            sentiment_values.append(value)
        else:
            sentiment_values.extend(value)

        # highlight_letter_for_sentiment always returns a list, so use extend
        highlighted_letters.extend(highlighted_letter)

    results = zip(sentiment_values, highlighted_letters)
    return render(request, 'letter_sentiment.html',
                  {'title': 'Letter Sentiment', 'nbar': 'sentiment', 'letter': letter,
                   'results': results})


def highlight_letter_for_sentiment(letter, sentiment_id):
    # highlight_for_sentiment() returns a list,
    # for the case of multiple different positive/negative sentiments
    highlighted_letters = []

    headings = highlight_for_sentiment(letter.heading, sentiment_id)
    greetings = highlight_for_sentiment(letter.greeting, sentiment_id)
    bodies = highlight_for_sentiment(letter.body_as_text(), sentiment_id)
    closings = highlight_for_sentiment(letter.closing, sentiment_id)
    sigs = highlight_for_sentiment(letter.signature, sentiment_id)
    pss = highlight_for_sentiment(letter.ps, sentiment_id)

    for idx, heading in enumerate(headings):
        # Make a copy of the letter so we can manipulate the content fields
        highlighted_letter = deepcopy(letter)
        highlighted_letter.pk = None
        highlighted_letter.heading = mark_safe(heading)
        highlighted_letter.greeting = mark_safe(greetings[idx])
        highlighted_letter.body = mark_safe(bodies[idx])
        highlighted_letter.closing = mark_safe(closings[idx])
        highlighted_letter.signature = mark_safe(sigs[idx])

        highlighted_letter.ps = mark_safe(pss[idx])

        highlighted_letters.append(highlighted_letter)

    return highlighted_letters


class TextSentimentView(TemplateView):
    """
    View to get a piece of text for analysis using the chosen sentiment(s)
    """

    template_name = 'text_sentiment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sort_by = [(DATE, 'Date')]
        sort_by.extend(get_sentiments_for_sort_by_list())

        context['title'] = 'Text sentiment'
        context['nbar'] = 'sentiment'
        context['filter_values'] = letters_filter.get_initial_filter_values()

        return context


class GetTextSentimentView(View):
    """
    Get sentiment analysis (and highlighting, if custom sentiment) for submitted text
    """

    def post(self, request, *args, **kwargs):
        sentiment_ids = letters_filter.get_filter_values_from_request(request).sentiment_ids
        text = request.POST.get('text')

        sentiments = []
        highlighted_texts = []

        try:
            for sentiment_id in sentiment_ids:
                highlighted_texts.extend(highlight_for_sentiment(text, sentiment_id))
                if sentiment_id == 0:
                    sentiments.extend(get_sentiment(text))
                else:
                    sentiments.append(get_custom_sentiment_for_text(text, sentiment_id))
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        results = zip(sentiments, highlighted_texts)
        sentiment_html = render_to_string('snippets/sentiment_list.html', {'results': results})

        # This was Ajax
        return HttpResponse(json.dumps({'sentiments': sentiment_html}), content_type="application/json")


def highlight_for_sentiment(text, sentiment_id):
    if sentiment_id == 0:
        return [mark_safe(highlight) for highlight in highlight_text_for_sentiment(text)]

    return [mark_safe(highlight_for_custom_sentiment(text, sentiment_id))]


class SearchView(View):
    """
    Return list of letters containing search text
    page_number is optional
    """

    def post(self, request, *args, **kwargs):
        if request.POST.get('search_text'):
            size = 5
        else:
            size = 10
        page_number = int(request.POST.get('page_number'))

        try:
            es_result = letter_search.do_letter_search(request, size, page_number)
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        result_html = render_to_string('snippets/search_list.html', {'search_results': es_result.search_results})
        # First request, no pagination yet
        if page_number == 0:
            # There is no built-in way to do something N times in a django template,
            # so generate a string of length <es_result.pages> and use that in the template
            # Yes, it's silly, but it's simpler than adding another template filter
            pages_string = 'x' * es_result.pages
            pagination_html = render_to_string('snippets/pagination.html',
                                               {'pages': pages_string, 'total': es_result.total})
        else:
            pagination_html = ''
        # This was Ajax
        return HttpResponse(json.dumps({
            'letters': result_html, 'pagination': pagination_html, 'pages': es_result.pages}),
            content_type="application/json")


class LetterDetailView(DetailView, ObjectNotFoundMixin):
    """
    Show one letter, by id
    """

    model = Letter
    context_object_name = 'letter'
    template_name = 'letter.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        letter = self.object
        letter.body = mark_safe(letter.body)
        context['title'] = 'Letter'
        context['nbar'] = 'letters_view'

        return context


# show particular letter
def show_letter_content(request, letter, title, nbar):
    letter.body = mark_safe(letter.body)
    return render(request, 'letter.html',
                  {'title': title, 'nbar': nbar, 'letter': letter})


def export_csv(letters):
    # write csv file contents to buffer rather than directly to HttpResponse
    # because that was causing SSL EOF errors
    buffer = StringIO()
    csv_writer = csv.writer(buffer)
    csv_writer.writerow(['date', 'writer', 'recipient', 'place', 'contents'])

    for letter in letters:
        date = letter.sort_date()
        writer = letter.writer.to_export_string()
        recipient = letter.recipient.to_export_string()
        place = letter.place
        contents = letter.contents()
        csv_writer.writerow([date, writer, recipient, place, contents])

    buffer.seek(0)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="letters_export.csv"'

    return response


def export_text(letters):
    text_to_export = ''
    for letter in letters:
        text_to_export += get_letter_export_text(letter) + '\r\n\r\n'

    # Create the HttpResponse object with the appropriate header.
    response = HttpResponse(text_to_export, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="letters_export.txt"'

    return response


# what gets exported for each letter
def get_letter_export_text(letter):
        return str.format('<{0}, {1} to {2}>\n{3}',
                          letter.index_date(), letter.writer.to_export_string(),
                          letter.recipient.to_export_string(), letter.contents())


def get_elasticsearch_error_response(exception, json_response=True):
    """
    Return HttpResponse with json containing url for Elasticsearch error page,
    or redirect to it
    """
    url = reverse('elasticsearch_error', kwargs={'error': exception.error,
                                                 'status': exception.status if exception.status else 0})
    if json_response:
        return HttpResponse(json.dumps({'redirect_url': url}), content_type="application/json")
    else:
        return redirect(url)


class RandomLetterView(View):
    """
    Retrieve a letter with a random index
    """

    def get(self, request, *args, **kwargs):
        count = Letter.objects.count()
        if count >= 1:
            random_idx = random.randint(0, count - 1)
            letter = Letter.objects.all()[random_idx]
            letter.body = mark_safe(letter.body)

            return render(request, 'letter.html',
                          {'letter': letter, 'title': 'Random letter', 'nbar': 'random_letter'})

        return object_not_found(request, 0, 'Letter')


class PlaceListView(ListView):
    """
    Show map of places
    """

    model = Place
    queryset = Place.objects.filter(point__isnull=False)[:100]
    template_name = 'places.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Places'
        context['nbar'] = 'places'
        context['filter_values'] = letters_filter.get_initial_filter_values()
        context['show_search_text'] = 'true'

        map_html = render_to_string('snippets/map.html', {'places': self.queryset})
        context['map'] = map_html

        return context


class PlaceSearchView(View):
    """
    Return map of places whose letters meet search criteria
    """

    def post(self, request, *args, **kwargs):
        # get a bunch of them!
        size = 5000
        # Search for letters that meet criteria. Start at beginning, so page number = 0
        try:
            es_result = letter_search.do_letter_search(request, size, page_number=0)
        except ElasticsearchException as ex:
            return get_elasticsearch_error_response(exception=ex, json_response=True)

        # Get list of corresponding places
        place_ids = set([letter.place_id for letter, highlight, sentiments, score in es_result.search_results])
        # Only show the first 100
        places = Place.objects.filter(pk__in=place_ids, point__isnull=False)[:100]
        map_html = render_to_string('snippets/map.html', {'places': places})
        # This was Ajax
        return HttpResponse(json.dumps({'map': map_html}), content_type="application/json")


class PlaceDetailView(DetailView, ObjectNotFoundMixin):
    """
    Show one place by id
    """

    model = Place
    context_object_name = 'place'
    template_name = 'place.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        letters = Letter.objects.filter(place=self.object).order_by('date')
        context['title'] = 'Place'
        context['nbar'] = 'places'
        context['letters'] = letters

        return context
