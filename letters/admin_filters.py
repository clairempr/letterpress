# Custom filters for Django Admin interface
from django.contrib.admin import SimpleListFilter
from django_date_extensions.fields import ApproximateDate
from .models import Correspondent, DocumentSource, Envelope, Letter, MiscDocument
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


def get_objects_with_date(model):
    return model.objects.exclude(date='')


def get_source_lookups():
    return DocumentSource.objects.values_list('id', 'name')


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


class MonthFilter(SimpleListFilter):
    title = 'month'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        """
        Lookups are all the months for which a dated model object exists
        """

        months = set([doc.date.month for doc in get_objects_with_date(model_admin.model)])
        return [(month, calendar.month_name[month]) for month in months]

    def queryset(self, request, queryset):
        """
        Return all the objects that have a date in the given month, if specified
        Otherwise return all the objects
        """

        if self.value():
            month = int(self.value())
            doc_ids = [doc.id for doc in get_objects_with_date(queryset.model) if doc.date.month == month]
            return queryset.filter(pk__in=doc_ids)
        else:
            return queryset


class RecipientFilter(SimpleListFilter):
    title = 'recipient'
    parameter_name = 'recipient'

    def lookups(self, request, model_admin):
        recipients = set([doc.recipient for doc in model_admin.model.objects.all()])
        return [(recipient.id, recipient.to_string()) for recipient in recipients]

    def queryset(self, request, queryset):
        if self.value():
            recipient = int(self.value())
            return queryset.filter(recipient=recipient)
        else:
            return queryset


class WriterFilter(SimpleListFilter):
    title = 'writer'
    parameter_name = 'writer'

    def lookups(self, request, model_admin):
        writers = set([doc.writer for doc in model_admin.model.objects.all()])
        return [(writer.id, writer.to_string()) for writer in writers]

    def queryset(self, request, queryset):
        if self.value():
            writer = int(self.value())
            return queryset.filter(writer=writer)
        else:
            return queryset


class YearFilter(SimpleListFilter):
    title = 'year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        years = set([doc.date.year for doc in get_objects_with_date(model_admin.model)])
        return [(year, year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            year = int(self.value())
            start_date = ApproximateDate(year=year, month=0, day=0)
            end_date = ApproximateDate(year=year, month=12, day=31)
            return queryset.filter(date__gte=start_date).filter(date__lte=end_date)
        else:
            return queryset
