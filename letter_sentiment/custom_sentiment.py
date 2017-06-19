from textblob import TextBlob

from letters.elasticsearch import get_sentiment_termvector_for_text
from letter_sentiment.models import CustomSentiment


def calculate_custom_sentiment(custom_sentiment_id, termvector, word_count):
    custom_sentiment = get_custom_sentiment(custom_sentiment_id)
    if not custom_sentiment or not custom_sentiment.get_terms():
        return 0

    name = custom_sentiment.name
    terms = sort_terms_by_number_of_words(custom_sentiment.get_terms())
    max_weight = custom_sentiment.max_weight
    sentiment = 0

    for term in terms:
        term_text = term.analyzed_text
        if term_text in termvector and 'term_freq' in termvector[term_text]:
            sentiment += (termvector[term_text]['term_freq'] * term.number_of_words() * term.weight)
            termvector = update_freqs_in_termvector(termvector, term)

    weight_factor = (max_weight + 1) / 2
    sentiment = (sentiment / weight_factor) / (word_count * .119) if word_count else 0

    return str.format('{0}: {1:.3f}', name, sentiment)


# get termvector and word count for text, and then call calculate_custom_sentiment
def calculate_custom_sentiment_for_text(text, custom_sentiment_id):
    termvector = get_sentiment_termvector_for_text(text)
    word_count = get_word_count_for_text(text)
    return calculate_custom_sentiment(custom_sentiment_id, termvector, word_count)


# surround relevant term in text with styled <span>
def highlight_text_for_custom_sentiment(text, custom_sentiment_id):
    custom_sentiment = get_custom_sentiment(custom_sentiment_id)
    if not custom_sentiment or not custom_sentiment.get_terms():
        return text

    highlight_normal_class = 'sentiment-highlight-normal'
    highlight_extra_class = 'sentiment-highlight-extra'

    highlighted_text = text

    terms = sort_terms_by_number_of_words(custom_sentiment.get_terms())
    termvector = get_sentiment_termvector_for_text(text)
    terms_to_place = {}

    for term in terms:
        term_text = term.analyzed_text
        if term_text in termvector and 'term_freq' in termvector[term_text]:

            if 'tokens' in termvector[term_text]:
                for token in termvector[term_text]['tokens']:
                    start, end, position = get_token_offsets(token)
                    terms_to_place[position] = (start, end, term.weight)
                    termvector = update_tokens_in_termvector(termvector, term, token)

    # offsets will be altered by insertions of highlighting markup,
    # depending on position in text, so start inserting at the end
    sorted_terms_to_place = [terms_to_place[pos] for pos in sorted(terms_to_place.keys(), reverse=True)]

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


def insert_highlight(highlighted_text, original_text, ss_start, ss_end, highlight_start, highlight_end):
    highlighted_term = str.format('{0}{1}{2}',
                                  highlight_start, original_text, highlight_end)

    # is term already surrounded by highlight markers?
    prev_highlight_start = highlighted_text.rfind(highlight_start, 0, ss_start)
    prev_highlight_end = highlighted_text.rfind(highlight_end, 0, ss_start)
    if prev_highlight_end > prev_highlight_start or prev_highlight_start == -1 or prev_highlight_end == -1:
        # not already surrounded, so insert them
        highlighted_text = do_highlight_replacement(highlighted_text, highlighted_term, ss_start, ss_end)

    return highlighted_text


def do_highlight_replacement(highlighted_text, highlighted_term, ss_start, ss_end):
    return str.format('{0}{1}{2}',
                      highlighted_text[:ss_start],
                      highlighted_term,
                      highlighted_text[ss_end:])


def update_freqs_in_termvector(termvector, term):
    words = term.analyzed_text.split(' ')
    for length in range(term.number_of_words() - 1, 0, -1):
        for word_idx in range(term.number_of_words() - (length - 1)):
            search_term = ' '.join(words[word_idx:word_idx + length])
            if search_term in termvector:
                termvector[search_term]['term_freq'] -= 1
                if termvector[search_term]['term_freq'] < 1:
                    del termvector[search_term]

    return termvector


def update_tokens_in_termvector(termvector, term, token):
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
                        # remove from termvector to make sure it doesn't get highlighted more than once
                        termvector[search_term]['tokens'].remove(search_token)
                        if len(termvector[search_term]['tokens']) < 1:
                            del termvector[search_term]

    return termvector


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


def get_word_count_for_text(text):
    blob_text = TextBlob(text)
    words = blob_text.words
    return len(words)