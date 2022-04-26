from django.db import models
from tinymce import models as tinymce_models

from letter_sentiment.sentiment import get_sentiment
from letters import es_settings
from letters.models import Correspondent, Document, Envelope, Place
from letters.models.util import get_envelope_preview, html_to_text


class Letter(Document):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Correspondent, on_delete=models.CASCADE, related_name='recipient')
    # letter content broken up into separate parts so it can be displayed more nicely
    heading = models.TextField(null=True, blank=True)
    greeting = models.TextField(null=True, blank=True)
    body = tinymce_models.HTMLField(null=True, blank=True)
    closing = models.TextField(null=True, blank=True)
    signature = models.TextField(null=True, blank=True)
    ps = models.TextField(null=True, blank=True)
    complete_transcription = models.BooleanField(default=False)
    envelopes = models.ManyToManyField(Envelope, blank=True)

    def get_display_string(self):
        return str.format('Letter: {0}, {1} to {2}',
                          self.list_date(), str(self.writer), str(self.recipient))

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def envelope_preview(self):
        return get_envelope_preview(self)

    # body without html markup
    def body_as_text(self):
        return html_to_text(self.body)

    # all the separate parts of the letter put together
    def contents(self):
        letter_contents = ''
        for part in [self.heading, self.greeting, self.body_as_text(), self.closing, self.signature, self.ps]:
            if part:
                letter_contents += part + '\n'
        return letter_contents

    def sentiment(self):
        return get_sentiment(self.contents())

    class Meta:
        # elasticsearch index stuff
        es_index_name = 'letterpress'
        es_type_name = 'letter'
        es_mapping = {
            "properties": {
                "contents": {"type": "text",
                             "analyzer": "letter_contents_analyzer",
                             "index_options": "offsets",
                             "term_vector": "with_positions_offsets",
                             "fields": {
                                 "word_count": {
                                     "type": "token_count",
                                     "analyzer": "string_sentiment_analyzer",
                                     "store": "yes"
                                 },
                                 "custom_sentiment": {
                                     "type": "text",
                                     "analyzer": "string_sentiment_analyzer",
                                     "term_vector": "with_positions_offsets"
                                 }
                             }
                        },
                "date": {
                    "type": "date",
                    # yyyy-MM-dd or yyyy-MM or yyyy
                    "format": "year_month_day||year_month||year",
                    "ignore_malformed": "false"
                },
                "source": {"type": "integer"},
                "writer": {"type": "integer"}
            }
        }

    def es_repr(self):
        """
        Serialize letter fields for Elasticsearch indexing by getting mapping from Meta
        and generating a representation of each field with field_es_repr

        See https://qbox.io/blog/elasticsearch-and-django-bulk-index/
        """

        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.pk
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data

    def field_es_repr(self, field_name):
        """
        Serialize letter field for Elasticsearch indexing:
        Get field description from mapping
        If there's a method named get_es_{field name} – use it to get field's value
        If it's an object, populate a dictionary directly from attributes of the related object
        If it's not an object, and there's no special method with special name, get an attribute from the model

        See https://qbox.io/blog/elasticsearch-and-django-bulk-index/
        """

        config = self._meta.es_mapping['properties'][field_name]
        if hasattr(self, 'get_es_%s' % field_name):
            field_es_value = getattr(self, 'get_es_%s' % field_name)()
        else:
            if config['type'] == 'object':
                related_object = getattr(self, field_name)
                field_es_value = {}
                field_es_value['_id'] = related_object.pk
                for prop in config['properties'].keys():
                    field_es_value[prop] = getattr(related_object, prop)
            else:
                field_es_value = getattr(self, field_name)
        return field_es_value

    def get_es_contents(self):
        return self.contents()

    def get_es_date(self):
        return self.index_date()

    def get_es_writer(self):
        return self.writer_id

    def get_es_source(self):
        return self.source_id

    def save(self, *args, **kwargs):
        is_new = self.pk
        super(Letter, self).save(*args, **kwargs)
        self.create_or_update_in_elasticsearch(is_new=is_new)

    def create_or_update_in_elasticsearch(self, is_new):
        """
        If this is a newly-created Letter that hasn't been assigned a pk yet,
        index it in Elasticsearch

        If it's an existing Letter, update the Elasticsearch index
        """

        es = es_settings.ES_CLIENT
        payload = self.es_repr()
        del payload['_id']
        if is_new is None:
            es.create(
                index=self._meta.es_index_name,
                doc_type=self._meta.es_type_name,
                id=self.pk,
                refresh=True,
                body=payload
            )
        else:
            es.update(
                index=self._meta.es_index_name,
                doc_type=self._meta.es_type_name,
                id=self.pk,
                refresh=True,
                body={
                    "doc": payload
                }
            )

    def delete(self, *args, **kwargs):
        pk = self.pk
        super(Letter, self).delete(*args, **kwargs)
        self.delete_from_elasticsearch(pk)

    def delete_from_elasticsearch(self, pk):
        es = es_settings.ES_CLIENT
        es.delete(
            index=self._meta.es_index_name,
            doc_type=self._meta.es_type_name,
            id=pk,
            refresh=True,
        )
