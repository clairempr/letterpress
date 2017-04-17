# Elasticsearch settings
from elasticsearch import Elasticsearch, RequestsHttpConnection
import letterpress.settings_secret as settings_secret


ES_SEARCH = settings_secret.ES_URL + 'letterpress/letter/_search'
ES_MTERMVECTORS = settings_secret.ES_URL + 'letterpress/letter/_mtermvectors'

ES_CLIENT = Elasticsearch(
    [settings_secret.ES_URL],
    connection_class=RequestsHttpConnection
)

# Settings for custom analyzer
AMPERSAND_REPLACEMENT = 'DHPEOPIJOJOIUYTUXBTEEXFGOPMBFR'

settings = {
    "analysis": {
        "analyzer": {
            "letter_contents_analyzer": {
                "char_filter": [
                    "hide_ampersand"
                ],
                "tokenizer": "standard",
                "filter": ["restore_ampersand", "lowercase"]
            }
        },
        "char_filter": {
            "hide_ampersand": {
                "type": "mapping",
                "mappings": [
                    "& => " + AMPERSAND_REPLACEMENT
                ]
            }
        },
        "filter": {
            "restore_ampersand": {
                "type": "pattern_replace",
                "pattern": AMPERSAND_REPLACEMENT,
                "replacement": "&"
            }
        }
    }}
