from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from letters.models import Letter, Place
import json
import random
from letters import elasticsearch, filter
from letters.charts import make_charts


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(request, 'letterpress.html', {'title': 'Letterpress', 'nbar': 'home'})


# show letters, with filters
def letters_view(request):
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        return export(request)
    filter_values = filter.get_initial_filter_values()
    return render(request, 'letters.html', {'title': 'Letters', 'nbar': 'letters_view',
                                            'filter_values': filter_values, 'search_text': 'true',
                                            'export_button': 'true'})


# Show page for requesting various stats about word use over time
def stats_view(request):
    assert isinstance(request, HttpRequest)
    filter_values = filter.get_initial_filter_values()
    return render(request, 'stats.html', {'title': 'Letter statistics', 'nbar': 'stats_view',
                                          'filter_values': filter_values, 'words': 'true'})


# Show stats for requested words/months, based on filter
def get_stats(request):
    assert isinstance(request, HttpRequest)
    if request.method != 'POST':
        return

    filter_values = filter.get_filter_values_from_request(request)
    es_word_counts = elasticsearch.get_word_counts_per_month(filter_values)
    words = filter_values.words
    es_word_freqs = elasticsearch.get_multiple_word_frequencies(filter_values)

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


# return list of letters containing search text
# page_number is optional
def search(request):
    assert isinstance(request, HttpRequest)
    if request.method != 'POST':
        return
    if request.POST.get('search_text'):
        size = 5
    else:
        size = 10
    page_number = int(request.POST.get('page_number'))
    es_result = elasticsearch.do_letter_search(request, size, page_number)
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


# view to show one letter by id
def letter_by_id(request, letter_id):
    assert isinstance(request, HttpRequest)
    try:
        letter = Letter.objects.get(pk=letter_id)
        return show_letter_content(request, letter, title='Letter', nbar='letters_view')
    except Letter.DoesNotExist:
        return object_not_found(request, letter_id, 'Letter')


def object_not_found(request, object_id, object_type):
    return render(request, 'obj_not_found.html',
                  {'title': object_type + ' not found', 'object_id': object_id, 'object_type': object_type})


# show particular letter
def show_letter_content(request, letter, title, nbar):
    letter.body = mark_safe(letter.body)
    description = letter.to_string()
    image_tags = [image.image_tag() for image in letter.images.all()]
    return render(request, 'letter.html',
                  {'title': title, 'nbar': nbar, 'letter': letter, 'description': description, 'images': image_tags})


# exports letters to output file
def export(request):
    assert isinstance(request, HttpRequest)
    # for export, return all matching records, within reason
    size = 10000
    es_result = elasticsearch.do_letter_search(request, size, page_number=0)
    letters = [letter for letter, highlight in es_result.search_results]
    text_to_export = ''
    for letter in letters:
        text_to_export += letter.export_text() + '\n\n'

    # Create the HttpResponse object with the appropriate header.
    response = HttpResponse(text_to_export, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="letters_export.txt"'

    return response


# retrieve a letter with a random index
def random_letter(request):
    random_idx = random.randint(0, Letter.objects.count() - 1)
    letter = Letter.objects.all()[random_idx]
    return show_letter_content(request, letter, title='Random letter', nbar='random_letter')


# Show map of places
def places_view(request):
    assert isinstance(request, HttpRequest)
    filter_values = filter.get_initial_filter_values()
    places = Place.objects.filter(point__isnull=False)[:100]
    map_html = render_to_string('snippets/map.html', {'places': places})
    return render(request, 'places.html', {'title': 'Places', 'nbar': 'places',
                                           'filter_values': filter_values, 'search_text': 'true',
                                           'map': map_html})


# return map of places whose letters meet search criteria
def search_places(request):
    assert isinstance(request, HttpRequest)
    if request.method != 'POST':
        return
    # get a bunch of them!
    size = 5000
    # Search for letters that meet criteria. Start at beginning, so page number = 0
    es_result = elasticsearch.do_letter_search(request, size, page_number=0)
    # Get list of corresponding places
    place_ids = set([letter.place_id for letter, highlight in es_result.search_results])
    # Only show the first 100
    places = Place.objects.filter(pk__in=place_ids, point__isnull=False)[:100]
    map_html = render_to_string('snippets/map.html', {'places': places})
    # This was Ajax
    return HttpResponse(json.dumps({'map': map_html}), content_type="application/json")


# view to show one place by id
def place_by_id(request, place_id):
    assert isinstance(request, HttpRequest)
    try:
        place = Place.objects.get(pk=place_id)
        letters = Letter.objects.filter(place=place_id)
        return render(request, 'place.html',
                      {'title': 'Place', 'nbar': 'place', 'place': place, 'letters': letters})
    except Place.DoesNotExist:
        return object_not_found(request, place_id, 'Place')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')
