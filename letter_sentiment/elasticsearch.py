""" Elasticsearch-specific functionality for custom sentiment calculations """
import json

from letter_sentiment.models import CustomSentiment
from letters.elasticsearch import do_es_search
from letters.models import Letter


# Use Elasticsearch scoring to calculate custom sentiment
def calculate_custom_sentiment(letter_id, sentiment_id):
    custom_sentiment_es = 0
    query = get_custom_sentiment_query(letter_id, sentiment_id)
    result = do_es_search(index=[Letter._meta.es_index_name], query=json.dumps(query))
    # get the score from the first hit (there should be only one)
    if 'hits' in result and 'hits' in result['hits']:
        custom_sentiment_es = result['hits']['hits'][0]['_score']

    return custom_sentiment_es


def get_custom_sentiment_query(letter_id, sentiment_id):
    # get the query with all the custom sentiment terms in it
    sentiment_match_query = get_sentiment_match_query(sentiment_id)
    should_conditions = [condition for condition in [sentiment_match_query] if condition]

    # filter by id
    bool_query = {
        "should": should_conditions,
        "must": {
            "terms": {
                "_id": [str(letter_id)]
            }
        }
    }

    # when calculating custom sentiment score, wrap the bool query in a function_score query
    query = {
        "function_score": get_sentiment_function_score_query(bool_query)
    }

    return {
        "query": query,
        "stored_fields": ["contents.word_count"]
    }


def get_sentiment_function_score_query(bool_query):
    return {
        "query":
            {
                "bool": bool_query
            },
        "script_score": {
            "script": {
                "lang": "painless",
                # _score of 1 means that no terms were found, so return 0
                "inline": "if (_score == 1) { return 0; } "
                          "long word_count = doc['contents.word_count'].value; "
                          "double factor = (Math.log(word_count * 0.5) / Math.log(2)) * 14; "
                          "return _score / factor;"
            }
        }
    }


def get_sentiment_match_query(sentiment_id):
    sentiment_match_query = []

    try:
        my_custom_sentiment = CustomSentiment.objects.get(pk=sentiment_id)
    except CustomSentiment.DoesNotExist:
        my_custom_sentiment = None

    if my_custom_sentiment:
        max_weight = my_custom_sentiment.max_weight
        terms = my_custom_sentiment.get_terms()
        for term in terms:
            boost = term.weight * term.number_of_words() / max_weight
            term_match_query = {'match_phrase':
                                    {'contents.custom_sentiment':
                                         {'query': term.text,
                                          'boost': boost,
                                         }
                                    }
                               }

            sentiment_match_query.append(term_match_query)

    return sentiment_match_query
