from django.contrib import admin
from django.contrib.gis import admin as gisAdmin
from .models import Correspondent, Place, Letter, DocumentImage, DocumentSource, Envelope, MiscDocument
from letters.admin_filters import CorrespondentSourceFilter, ImageSourceFilter, MonthFilter, \
    RecipientFilter, WriterFilter, YearFilter


# Model admin classes

# This subclass of Django ModelAdmin contains settings that are
# needed in all my model admin classes
class MyModelAdmin(admin.ModelAdmin):
    # show Save and Delete buttons at the top of the page as well as at the bottom
    save_on_top = True
    fields = ('id',)
    readonly_fields = ('id',)


# Contains settings that are needed in admin classes for all models
# that inherit from Document
class DocumentAdmin(MyModelAdmin):
    fields = ('id', 'source', 'date',)
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images',)
    list_display = ('list_date',)
    list_filter = ('source', WriterFilter, YearFilter, MonthFilter,)
    ordering = ('date',)


class CorrespondentAdmin(MyModelAdmin):
    fields = MyModelAdmin.fields + (
        'last_name', 'married_name', 'first_names', 'suffix', 'aliases',
        'description', 'images', 'image_preview',
    )
    ordering = ('last_name', 'first_names', 'suffix')
    readonly_fields = MyModelAdmin.readonly_fields + ('image_preview',)
    filter_horizontal = ('images',)
    list_filter = [CorrespondentSourceFilter,]


class LetterInline(admin.TabularInline):
    model = Letter.envelopes.through
    raw_id_fields = ('letter',)
    extra = 0


class EnvelopeAdmin(DocumentAdmin):
    fields = DocumentAdmin.fields + ('description', 'writer', 'origin', 'recipient',
                                     'destination', 'contents', 'notes', 'images', 'image_preview',)
    ordering = DocumentAdmin.ordering + ('description',)
    list_display = DocumentAdmin.list_display + ('description',)
    list_filter = DocumentAdmin.list_filter + (RecipientFilter, )
    inlines = [LetterInline]


class LetterAdmin(DocumentAdmin):
    fields = DocumentAdmin.fields + (
        'place', 'writer', 'recipient', 'heading',
        'greeting', 'body', 'closing', 'signature', 'ps', 'language',
        'complete_transcription', 'notes', 'images', 'image_preview',
        'envelopes', 'envelope_preview'
    )
    ordering = DocumentAdmin.ordering + ('writer__last_name', 'writer__first_names',
                                         'writer__suffix')
    list_display = DocumentAdmin.list_display + ('writer', 'recipient', 'place')
    list_filter = DocumentAdmin.list_filter + ('place', RecipientFilter, )
    readonly_fields = DocumentAdmin.readonly_fields + ('envelope_preview',)
    search_fields = ('writer__last_name', 'writer__first_names',
                     'recipient__last_name', 'recipient__first_names',
                     'place__name',  'place__state', 'date')
    filter_horizontal = DocumentAdmin.filter_horizontal + ('envelopes',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(LetterAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['heading'].widget.attrs['style'] = 'height: 5em;'
        form.base_fields['greeting'].widget.attrs['style'] = 'height: 3em;'
        form.base_fields['closing'].widget.attrs['style'] = 'height: 3em;'
        form.base_fields['signature'].widget.attrs['style'] = 'height: 3em;'
        form.base_fields['ps'].widget.attrs['style'] = 'height: 3em;'
        return form

    # Override Django Admin's delete_queryset action to use model's
    # delete method and update elasticsearch index
    # Unfortunately, we lose the confirmation dialogue
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


class DocumentImageAdmin(MyModelAdmin):
    ordering = ('description', 'type', 'image_file', )
    list_display = ('__str__', 'type', 'thumbnail',)
    list_filter = ('type', ImageSourceFilter)
    fields = ('description', 'type', 'image_file', 'image_tag',)
    readonly_fields = ('image_tag',)


class DocumentSourceAdmin(MyModelAdmin):
    fields = ('id', 'name', 'description', 'url', 'images', 'image_preview',)
    ordering = ('name',)
    readonly_fields = ('id', 'image_preview',)
    filter_horizontal = ('images',)


class MiscDocumentAdmin(DocumentAdmin):
    fields = DocumentAdmin.fields + ('description', 'writer', 'place', 'contents', 'notes', 'images',
                                     'image_preview', 'envelopes', 'envelope_preview')

    readonly_fields = DocumentAdmin.readonly_fields + ('envelope_preview',)
    filter_horizontal = DocumentAdmin.filter_horizontal + ('envelopes',)
    list_display = DocumentAdmin.list_display + ('description',)
    list_filter = DocumentAdmin.list_filter + ('place',)
    ordering = DocumentAdmin.ordering + ('description',)


class PlaceAdmin(gisAdmin.OSMGeoAdmin):
    # show Save and Delete buttons at the top of the page as well as at the bottom
    save_on_top = True
    fields = ['id', 'name', 'state', 'country', 'point', 'notes']
    readonly_fields = ['id']
    default_lon = -8635591.130572217
    default_lat = 4866434.335995871
    default_zoom = 5
    ordering = ('name', 'state', 'country',)
    list_filter = ['country', 'state']
    openlayers_url = 'https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.15.1/build/ol.js'
    map_template = 'admin/place_admin_map.html'


admin.site.register(Correspondent, CorrespondentAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Letter, LetterAdmin)
admin.site.register(DocumentImage, DocumentImageAdmin)
admin.site.register(DocumentSource, DocumentSourceAdmin)
admin.site.register(Envelope, EnvelopeAdmin)
admin.site.register(MiscDocument, MiscDocumentAdmin)
