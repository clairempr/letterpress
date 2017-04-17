from django.db import models
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from django_date_extensions.fields import ApproximateDateField
from bs4 import BeautifulSoup
from tinymce import models as tinymce_models
import django.db.models.options as options
from letters import es_settings

options.DEFAULT_NAMES += 'es_index_name', 'es_type_name', 'es_mapping'
DEFAULT_COUNTRY = 'US'
DEFAULT_LANGUAGE = 'EN'


class DocumentImage(models.Model):
    IMAGE_TYPES = (
        ('L', 'Letter'),
        ('E', 'Envelope'),
        ('T', 'Transcription'),
        ('D', 'Other document'),
    )
    description = models.CharField(max_length=75, blank=True)
    type = models.CharField(max_length=1, choices=IMAGE_TYPES)
    image_file = models.ImageField(upload_to='letter_images')

    def __str__(self):
        if self.description:
            return self.description
        else:
            return str.format('Image: {0}', str(self.image_file.name))

    def get_url(self):
        return settings.MEDIA_URL + self.image_file.name

    def image_tag(self):
        return self.image_preview_with_link(400)

    image_tag.short_description = 'Image'

    def thumbnail(self):
        return self.image_preview_with_link(100)

    def image_preview_with_link(self, height):
        if self.image_file:
            html = str.format('<a href="{0}"><img src="{1}" height="{2}" /></a>',
                              self.get_url(), self.get_url(), height)
            return mark_safe(html)
        else:
            return 'No image'


class DocumentSource(models.Model):
    name = models.CharField(max_length=75, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def to_string(self):
        return self.name

    def image_preview(self):
        return get_image_preview(self)


class Correspondent(models.Model):
    last_name = models.CharField(max_length=50, blank=True)
    married_name = models.CharField(max_length=50, blank=True)
    first_names = models.CharField(max_length=75, blank=True)
    suffix = models.CharField(max_length=10, blank=True)
    aliases = models.CharField(max_length=75, blank=True)
    description = models.TextField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.get_display_string()

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        desc = str.format('{last_name}{comma}{first_names}{married_name}{suffix}',
                          last_name=self.last_name,
                          comma=', ' if self.last_name and self.first_names else '',
                          first_names=self.first_names,
                          married_name=' (' + self.married_name + ')' if self.married_name else '',
                          suffix=', ' + self.suffix if self.suffix else '')
        return desc

    def to_export_string(self):
        desc = str.format('{0} {1}', self.first_names, self.last_name)
        if self.suffix:
            desc += ', ' + self.suffix
        return desc

    def image_preview(self):
        return get_image_preview(self)


class Place(models.Model):
    name = models.CharField(max_length=75, blank=True)
    state = models.CharField(max_length=2, blank=True)
    country = models.CharField(max_length=2, default=DEFAULT_COUNTRY, blank=True)
    # Geo Django field to store a point
    point = models.PointField(help_text='Represented as (longitude, latitude)', null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        desc = self.name
        if self.state:
            desc += ', ' + self.state
        if self.country != DEFAULT_COUNTRY:
            desc += ', ' + self.country
        return desc


class Letter(models.Model):
    date = ApproximateDateField(null=True)
    place = models.ForeignKey(Place)
    writer = models.ForeignKey(Correspondent, related_name='writer')
    recipient = models.ForeignKey(Correspondent, related_name='recipient')
    source = models.ForeignKey(DocumentSource)
    # letter content broken up into separate parts so it can be displayed more nicely
    heading = models.TextField(null=True, blank=True)
    greeting = models.TextField(null=True, blank=True)
    body = tinymce_models.HTMLField(null=True, blank=True)
    closing = models.TextField(null=True, blank=True)
    signature = models.TextField(null=True, blank=True)
    ps = models.TextField(null=True, blank=True)
    complete_transcription = models.BooleanField(default=False)
    notes = tinymce_models.HTMLField(blank=True)
    language = models.CharField(max_length=2, default=DEFAULT_LANGUAGE, blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return str.format('Letter: {0}, {1} to {2}',
                          self.list_date(), str(self.writer), str(self.recipient))

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def to_string(self):
        return str.format('Letter: {0}, {1} to {2}',
                          self.list_date(), str(self.writer), str(self.recipient))

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

    def image_preview(self):
        return get_image_preview(self)

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


class Envelope(models.Model):
    source = models.ForeignKey(DocumentSource)
    description = models.CharField(max_length=75, blank=True)
    date = ApproximateDateField(null=True)
    writer = models.ForeignKey(Correspondent, related_name='envelope_writer')
    origin = models.ForeignKey(Place, related_name='origin')
    recipient = models.ForeignKey(Correspondent, related_name='envelope_recipient')
    destination = models.ForeignKey(Place, related_name='destination')
    contents = tinymce_models.HTMLField(null=True, blank=True)
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.get_display_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        if self.description:
            return self.description

        return str.format('{writer} to {recipient}{date}',
                          writer=self.writer,
                          recipient=self.recipient,
                          date=', ' + self.date if self.date else '')

    def image_preview(self):
        return get_image_preview(self)


class MiscDocument(models.Model):
    source = models.ForeignKey(DocumentSource)
    description = models.CharField(max_length=75)
    date = ApproximateDateField(null=True)
    writer = models.ForeignKey(Correspondent, related_name='miscdoc_writer')
    place = models.ForeignKey(Place)
    contents = tinymce_models.HTMLField(null=True, blank=True)
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.get_display_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        return self.description

    def image_preview(self):
        return get_image_preview(self)


def get_image_preview(obj):
    return mark_safe('&nbsp;'.join([image.image_tag() for image in obj.images.all()]))


def html_to_text(html):
    # Convert the html content into a beautiful soup object
    soup = BeautifulSoup(html,
                         'lxml')  # use 'lxml' instead of 'html.parser' for speed  # make sure we don't lose our line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    # Get plain text
    return soup.get_text()
