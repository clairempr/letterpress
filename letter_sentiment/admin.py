from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
from .models import Term, CustomSentiment


# Custom filters for Django Admin interface
class FirstLetterFilter(SimpleListFilter):
    title = 'first letter'
    parameter_name = 'term'

    def lookups(self, request, model_admin):
        chars = list(map(chr, range(97, 123)))
        return [(char, char.upper()) for char in chars]

    def queryset(self, request, queryset):
        if self.value():
            char = self.value()
            term_ids = [term.id for term in queryset.model.objects.all() if term.text.startswith(char)]
            return queryset.filter(pk__in=term_ids)
        else:
            return queryset


# Model admin classes
class TermAdmin(admin.ModelAdmin):
    list_display = ('text', 'analyzed_text', 'weight')
    list_filter = ('custom_sentiment', FirstLetterFilter, 'weight')
    search_fields = ('text',)
    fields = ('id', 'custom_sentiment', 'text', 'analyzed_text', 'weight')
    readonly_fields = ('id', 'analyzed_text',)


class TermInline(admin.TabularInline):
    model = Term
    extra = 3
    can_delete = True
    fields = ('text', 'analyzed_text_display', 'weight')
    readonly_fields = ('analyzed_text_display',)

    def analyzed_text_display(self, obj):
        analyzed_text = obj.analyzed_text
        if obj.text == analyzed_text:
            display = analyzed_text
        else:
            display = mark_safe(str.format('<span style="color:red;">{0}</span>', analyzed_text))
        return display


class CustomSentimentAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = (TermInline,)


admin.site.register(CustomSentiment, CustomSentimentAdmin)
admin.site.register(Term, TermAdmin)


