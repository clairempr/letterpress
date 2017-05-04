from django.db import models
from tinymce import models as tinymce_models
from letters.models import Correspondent, Document, Envelope, Place
from letters.models.util import get_envelope_preview, html_to_text
from letters import es_settings


class Letter(Document):
    place = models.ForeignKey(Place)
    recipient = models.ForeignKey(Correspondent, related_name='recipient')
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

    # return formatted date with separators and unknown elements filled with '?'
    def list_date(self):
        my_year = '{:0>4}'.format(self.date.year) if self.date.year else '????'
        my_month = '{:0>2}'.format(self.date.month) if self.date.month else '??'
        my_day = '{:0>2}'.format(self.date.day) if self.date.day else '??'
        return str.format('{0}-{1}-{2}', my_year, my_month, my_day)

    # return date in the format yyyymmdd with zeroes in unknown elements
    def sort_date(self):
        return str.format('{:0>4}{:0>2}{:0>2}', self.date.year, self.date.month, self.date.day)

    # return date in the format yyyy-MM-dd or yyyy-MM or yyyy for elasticsearch index
    def index_date(self):
        index_date = str.format('{:0>4}', self.date.year)
        if self.date.month:
            index_date += str.format('-{:0>2}', self.date.month)
        if self.date.day:
            index_date += str.format('-{:0>2}', self.date.day)
        return index_date

    # all the separate parts of the letter put together
    def contents(self):
        letter_contents = ''
        for part in [self.heading, self.greeting, html_to_text(self.body), self.closing, self.signature, self.ps]:
            if part:
                letter_contents += part + '\n'
        return letter_contents

    # what gets exported for each letter
    def export_text(self):
        return str.format('<{0}, {1} to {2}>\n{3}',
                          self.list_date(), self.writer.to_export_string(),
                          self.recipient.to_export_string(), self.contents())

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
                                     "analyzer": "letter_contents_analyzer",
                                     "store": "yes"
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
        data = {}
        mapping = self._meta.es_mapping
        data['_id'] = self.pk
        for field_name in mapping['properties'].keys():
            data[field_name] = self.field_es_repr(field_name)
        return data

    def field_es_repr(self, field_name):
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
        es = es_settings.ES_CLIENT
        is_new = self.pk
        super(Letter, self).save(*args, **kwargs)
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