"""functions for calculating custom sentiment of letters and other text"""

from letters.elasticsearch import get_sentiment_termvector_for_text, \
    index_temp_document, delete_temp_document
from letter_sentiment.models import CustomSentiment
from letter_sentiment.elasticsearch import calculate_custom_sentiment
from letter_sentiment.sentiment import format_sentiment


# temporarily index text as contents of letter and calculate custom sentiment for that letter
def get_custom_sentiment_for_text(text, custom_sentiment_id):
    index_temp_document(text)
    sentiment = get_custom_sentiment_for_letter('temp', custom_sentiment_id)
    delete_temp_document()
    return sentiment


def get_custom_sentiment_for_letter(letter_id, custom_sentiment_id):
    custom_sentiment = get_custom_sentiment(custom_sentiment_id)
    if not custom_sentiment or not custom_sentiment.get_terms():
        return 0

    sentiment = calculate_custom_sentiment(letter_id, custom_sentiment_id)

    return format_sentiment(custom_sentiment.name, sentiment)


# surround relevant term in text with styled <span>
def highlight_for_custom_sentiment(text, custom_sentiment_id):
    custom_sentiment = get_custom_sentiment(custom_sentiment_id)
    if not custom_sentiment or not custom_sentiment.get_terms():
        return text

    highlight_normal_class = 'sentiment-highlight-normal'
    highlight_extra_class = 'sentiment-highlight-extra'

    highlighted_text = text

    terms = sort_terms_by_number_of_words(custom_sentiment.get_terms())
    termvector = get_sentiment_termvector_for_text(text)
    terms_to_place = {}

    # Look for terms in text's termvector
    # If an n-gram of the term is inside the token, remove that n-gram's token,
    # because we're interested in the most complete occurrence of the term
    for term in terms:
        term_text = term.analyzed_text
        if term_text in termvector and 'term_freq' in termvector[term_text]:

            if 'tokens' in termvector[term_text]:
                for token in termvector[term_text]['tokens']:
                    start, end, position = get_token_offsets(token)
                    terms_to_place[position] = (start, end, term.weight)
                    termvector = update_tokens_in_termvector(termvector, term, token)

    # Offsets will be altered by insertions of highlighting markup,
    # depending on position in text, so start inserting at the end
    sorted_terms_to_place \
        = [terms_to_place[pos] for pos in sorted(terms_to_place.keys(), reverse=True)]

    # If there are overlapping terms in the text, adjust start or end position of one of them
    prev_start_pos = 0
    for idx, (start_pos, end_pos, weight) in enumerate(sorted_terms_to_place):
        if prev_start_pos and end_pos > prev_start_pos:
            new_end = prev_start_pos - 1
            sorted_terms_to_place[idx] = (start_pos, new_end, weight)
        prev_start_pos = start_pos

    # Apply css classes for highlighting
    for start_pos, end_pos, weight in sorted_terms_to_place:
        highlight_class = highlight_normal_class if weight == 1 else highlight_extra_class
        highlighted_text = str.format('{0}<span class="{1}">{2}</span>{3}',
                                      highlighted_text[:start_pos],
                                      highlight_class,
                                      highlighted_text[start_pos:end_pos],
                                      highlighted_text[end_pos:])

    return highlighted_text


def get_token_offsets(token):
    start_offset = token['start_offset'] if 'start_offset' in token else 0
    end_offset = token['end_offset'] if 'end_offset' in token else 0
    position = token['position'] if 'position' in token else 0
    return start_offset, end_offset, position


def update_tokens_in_termvector(termvector, term, token):
    """
    Do something-or-other with termvector

    If an n-gram of the term is inside the token, remove that n-gram's token,
    because we're interested in the most complete occurrence of the term
    At least, I think that's what this does

    Because termvector is a dict, it gets passed in by reference and is updated in place, so
    the return value is kinda pointless
    """

    words = term.analyzed_text.split(' ')
    start, end, position = get_token_offsets(token)

    for length in range(term.number_of_words() - 1, 0, -1):
        for word_idx in range(term.number_of_words() - (length - 1)):
            search_term = ' '.join(words[word_idx:word_idx + length])
            if search_term in termvector:
                for search_token in termvector[search_term]['tokens']:
                    search_start, search_end, search_pos = get_token_offsets(search_token)
                    # does search_token occur inside token?
                    if start <= search_start and search_end <= end:
                        # remove from termvector to make sure it doesn't get highlighted
                        # more than once
                        termvector[search_term]['tokens'].remove(search_token)
                        if len(termvector[search_term]['tokens']) < 1:
                            del termvector[search_term]

    return termvector


def get_custom_sentiment_name(custom_sentiment_id):
    custom_sentiment = get_custom_sentiment(custom_sentiment_id)
    if custom_sentiment:
        return custom_sentiment.name

    return ''


def get_custom_sentiment(custom_sentiment_id):
    try:
        sentiment_obj = CustomSentiment.objects.get(pk=custom_sentiment_id)
    except CustomSentiment.DoesNotExist:
        sentiment_obj = None

    return sentiment_obj


def get_custom_sentiments():
    return CustomSentiment.objects.all()


def get_analyzed_custom_sentiment_terms(custom_sentiment_id):
    sentiment_obj = get_custom_sentiment(custom_sentiment_id)
    if sentiment_obj:
        return [term.analyzed_text for term in sentiment_obj.terms.all()]
    else:
        return []


def sort_terms_by_number_of_words(terms):
    terms_dict = {}
    for term in terms:
        if term.number_of_words() not in terms_dict:
            terms_dict[term.number_of_words()] = [term]
        else:
            terms_dict[term.number_of_words()].append(term)

    sorted_terms = []
    for num in sorted(terms_dict.keys(), reverse=True):
        sorted_terms.extend(terms_dict[num])
    return sorted_terms
