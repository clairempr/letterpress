# Elasticsearch settings
from elasticsearch import Elasticsearch, RequestsHttpConnection

from django.conf import settings


ES_LETTER_URL = settings.ELASTICSEARCH_URL + 'letterpress/letter/'
ES_ANALYZE = settings.ELASTICSEARCH_URL + 'letterpress/_analyze'
ES_SEARCH = ES_LETTER_URL + '_search?explain'
ES_MTERMVECTORS = ES_LETTER_URL + '_mtermvectors'

ES_CLIENT = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_URL],
)

# Settings for custom analyzer
AMPERSAND_REPLACEMENT = 'DHPEOPIJOJOIUYTUXBTEEXFGOPMBFR'

settings = {
    "analysis": {
        "analyzer": {
            # For analyzing letter contents to put in the index and use for text searching
            "letter_contents_analyzer": {
                "char_filter": ["hide_ampersand"],
                "tokenizer": "standard",
                "filter": ["restore_ampersand", "lowercase"]
            },
            # For analyzing custom sentiment search terms
            "string_sentiment_analyzer": {
                "char_filter": ["ampersand_to_and", "remove_apostrophes"],
                "tokenizer": "standard",
                "filter": ["lowercase", "kstem"]
            },
            # For (re)analyzing letter contents (sometimes html) when generating termvectors for
            # calculating or highlighting custom sentiment
            "termvector_sentiment_analyzer": {
                "char_filter": ["html_strip", "ampersand_to_and", "remove_apostrophes"],
                "tokenizer": "standard",
                "filter": ["lowercase", "kstem", "termvector_shingle_filter"]
            }
        },
        "char_filter": {
            "hide_ampersand": {
                "type": "mapping",
                "mappings": [
                    "& => " + AMPERSAND_REPLACEMENT
                ]
            },
            "ampersand_to_and": {
                "type": "mapping",
                "mappings": [
                    "& => and",
                ]
            },
            "remove_apostrophes": {
                "type": "mapping",
                "mappings": [
                    "' => "
                ]
            }
        },
        "filter": {
            "restore_ampersand": {
                "type": "pattern_replace",
                "pattern": AMPERSAND_REPLACEMENT,
                "replacement": "&"
            },
            "termvector_shingle_filter": {
                "type": "shingle",
                "max_shingle_size": 3,
                "min_shingle_size": 2,
                "output_unigrams": "true"
            }
        }
    }}
