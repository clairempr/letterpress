# Each custom sentiment has a list of relevant terms,
# each of which has an optional weight assigned

from django.db import models

from letters.elasticsearch import analyze_term


class CustomSentiment(models.Model):
    name = models.CharField(max_length=50, blank=True)
    max_weight = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    def get_terms(self):
        return self.terms.all()


class Term(models.Model):
    text = models.CharField(max_length=100)
    analyzed_text = models.CharField(max_length=100, default='', blank=True)
    custom_sentiment = models.ForeignKey(CustomSentiment, on_delete=models.CASCADE, related_name='terms')
    weight = models.IntegerField(default=1)

    __original_text = None

    def __init__(self, *args, **kwargs):
        super(Term, self).__init__(*args, **kwargs)
        self.__original_text = self.text

    def __str__(self):
        return self.text

    def number_of_words(self):
        return self.text.count(' ') + 1

    def save(self, *args, **kwargs):
        if (self.text != self.__original_text) or not self.analyzed_text:
            self.analyzed_text = analyze_text(self.text)
        super(Term, self).save(*args, **kwargs);
        self.__original_text = self.text

    class Meta:
        ordering = ('text',)


def analyze_text(text):
    return analyze_term(text, analyzer='string_sentiment_analyzer')