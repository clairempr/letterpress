# Elasticsearch settings
import ssl

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient

from django.conf import settings

from letterpress import settings_secret

ES_LETTER_URL = settings.ELASTICSEARCH_URL + 'letterpress/letter/'

# If no options are given and the certifi package is installed then certifi’s CA
# bundle is used by default:
# https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/config.html#tls-and-ssl
ES_CLIENT = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_URL],
    http_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
    verify_certs=False,
    ssl_version=ssl.TLSVersion.TLSv1_3
)

ES_INDICES_CLIENT = IndicesClient

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
