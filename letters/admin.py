from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin as gisAdmin
from django_date_extensions.fields import ApproximateDate
from .models import Correspondent, Place, Letter, DocumentImage, DocumentSource, Envelope, MiscDocument
import calendar


# get unique list of Correspondent ids associated with a DocumentSource id
# through letters, envelopes, and misc. documents
def get_correspondents_of_source(source):
    corr_ids = set(miscdoc.writer_id for miscdoc in MiscDocument.objects.filter(source_id=source))
    for letter in Letter.objects.filter(source_id=source):
        corr_ids.add(letter.writer_id)
        corr_ids.add(letter.recipient_id)
    for envelope in Envelope.objects.filter(source_id=source):
        corr_ids.add(envelope.writer_id)
        corr_ids.add(envelope.recipient_id)
    return corr_ids


def get_source_lookups():
    sources = set([doc_source for doc_source in DocumentSource.objects.all()])
    return [(source.id, source.name) for source in sources]


# Override Django Admin's delete_selected action to use model's
# delete method and update elasticsearch index
# Unfortunately, we lose the confirmation dialogue
def delete_selected(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()


# Get all Correspondents associated with a particular DocumentSource
class CorrespondentSourceFilter(SimpleListFilter):
    title = 'source'
    parameter_name = 'source'

    # Return list of all DocumentSources
    def lookups(self, request, model_admin):
        return get_source_lookups()

    # Get all Correspondents associated with a particular DocumentSource
    # by finding out which Correspondents were writers or recipients of
    # Letters, Envelopes, and MiscDocuments with this DocumentSource
    def queryset(self, request, queryset):
        if self.value():
            source = int(self.value())
            corr_ids = get_correspondents_of_source(source)
            return queryset.filter(pk__in=corr_ids)
        else:
            return queryset


class CorrespondentAdmin(admin.ModelAdmin):
    fields = ('id', 'last_name', 'married_name', 'first_names', 'suffix', 'description', 'images', 'image_preview',)
    ordering = ('last_name', 'first_names', 'suffix')
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images',)
    list_filter = [CorrespondentSourceFilter,]


class EnvelopeAdmin(admin.ModelAdmin):
    fields = ('id', 'source', 'description', 'date', 'writer', 'origin', 'recipient',
              'destination', 'contents', 'notes', 'images', 'image_preview')
    ordering = ('date', 'description')
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images',)


class ImageSourceFilter(SimpleListFilter):
    title = 'document source'
    parameter_name = 'source'

    # Return list of all DocumentSources
    def lookups(self, request, model_admin):
        return get_source_lookups()

    # Get all DocumentImages associated with a particular DocumentSource
    # by finding out which DocumentImages were images of
    # Letters, Envelopes, and MiscDocuments with this DocumentSource
    def queryset(self, request, queryset):
        if self.value():
            source = int(self.value())
            # Correspondents can have images, but they have no DocumentSource field,
            # so correspondents associated with a DocumentSource have to be searched for
            correspondent_ids = get_correspondents_of_source(source)
            image_ids = set()
            docs = [item for sublist in [MiscDocument.objects.filter(source_id=source),
                                         Letter.objects.filter(source_id=source),
                                         Envelope.objects.filter(source_id=source),
                                         Correspondent.objects.filter(pk__in=correspondent_ids)] for item in sublist]
            for doc in docs:
                image_ids.update(doc.images.values_list('id', flat=True))

            return queryset.filter(pk__in=set(image_ids))
        else:
            return queryset


class YearFilter(SimpleListFilter):
    title = 'year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        years = set([letter.date.year for letter in model_admin.model.objects.all()])
        return [(year, year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            year = int(self.value())
            start_date = ApproximateDate(year=year, month=0, day=0)
            end_date = ApproximateDate(year=year, month=12, day=31)
            return queryset.filter(date__gte=start_date).filter(date__lte=end_date)
        else:
            return queryset


class MonthFilter(SimpleListFilter):
    title = 'month'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        months = set([letter.date.month for letter in model_admin.model.objects.all()])
        return [(month, calendar.month_name[month]) for month in months]

    def queryset(self, request, queryset):
        if self.value():
            month = int(self.value())
            letter_ids = [letter.id for letter in Letter.objects.all() if letter.date.month == month]
            return queryset.filter(pk__in=letter_ids)
        else:
            return queryset


class LetterAdmin(admin.ModelAdmin):
    ordering = ('date', 'writer__last_name', 'writer__first_names', 'writer__suffix')
    list_display = ('list_date', 'writer', 'recipient', 'place')
    list_filter = ('source', YearFilter, MonthFilter, 'writer', 'recipient', 'place')
    fields = ('id', 'date', 'place', 'writer', 'recipient', 'source',
              'heading', 'greeting', 'body', 'closing', 'signature', 'ps', 'language',
              'complete_transcription', 'notes', 'images', 'image_preview', 'envelopes')
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images', 'envelopes')
    actions = [delete_selected]

    def get_form(self, request, obj=None, **kwargs):
        form = super(LetterAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['heading'].widget.attrs['style'] = 'height: 5em;'
        form.base_fields['greeting'].widget.attrs['style'] = 'height: 3em;'
        #form.base_fields['body'].widget.attrs['style'] = 'height: 18em;width: 49em;'
        form.base_fields['closing'].widget.attrs['style'] = 'height: 3em;'
        form.base_fields['signature'].widget.attrs['style'] = 'height: 3em;'
        form.base_fields['ps'].widget.attrs['style'] = 'height: 3em;'
        return form


class DocumentImageAdmin(admin.ModelAdmin):
    ordering = ('description', 'type', 'image_file', )
    list_display = ('__str__', 'type', 'thumbnail',)
    list_filter = ('type', ImageSourceFilter)
    fields = ('description', 'type', 'image_file', 'image_tag',)
    readonly_fields = ('image_tag',)


class DocumentSourceAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'description', 'url', 'images', 'image_preview',)
    ordering = ('name',)
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images',)


class PlaceAdmin(gisAdmin.OSMGeoAdmin):
    default_lon = -8635591.130572217
    default_lat = 4866434.335995871
    default_zoom = 5
    ordering = ('country', 'state', 'name')
    list_filter = ['country', 'state']
    openlayers_url = 'https://openlayers.org/en/v4.0.1/build/ol.js'
    map_template = 'admin/place_admin_map.html'


class MiscDocumentAdmin(admin.ModelAdmin):
    fields = ('id', 'source', 'description', 'date', 'writer', 'place', 'contents', 'notes', 'images', 'image_preview',
              'envelopes')
    ordering = ('date', 'description')
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images', 'envelopes',)


admin.site.register(Correspondent, CorrespondentAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Letter, LetterAdmin)
admin.site.register(DocumentImage, DocumentImageAdmin)
admin.site.register(DocumentSource, DocumentSourceAdmin)
admin.site.register(Envelope, EnvelopeAdmin)
admin.site.register(MiscDocument, MiscDocumentAdmin)
