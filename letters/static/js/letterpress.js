// Stuff to put CSRFToken in Ajax POST request
//var csrftoken = getCookie('csrftoken');
// Get token from form instead of from cookie,
// so we can use CSRF_COOKIE_HTTPONLY = True

var csrftoken = $('[name="csrfmiddlewaretoken"]').val();

function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

let filter_values = {

  get() {
    var sources = [];
    $('#sources input:checked').each(function () {
      sources.push(this.value);
    });
    var writers = [];
    $('#writers input:checked').each(function () {
      writers.push(this.value);
    });

    var start_date = $('#start_date').val();
    var end_date = $('#end_date').val();

    var search_text = $('#search_text').val();

    var words = [];
    if ($('#word1').val() != '') {
      words.push($('#word1').val());
    }
    if ($('#word2').val() != '') {
      words.push($('#word2').val());
    }

    var sentiments = selected_sentiments.get();
    var sort_by = selected_sort_by_option.get();

    return {
      sources: sources,
      writers: writers,
      sentiments: sentiments,
      start_date: start_date,
      end_date: end_date,
      search_text: search_text,
      words: words,
      sort_by: sort_by
    }
  }

}

let selected_sentiments = {

  get() {
    var sentiments = [];
    $('#sentiments input:checked').each(function () {
      sentiments.push(this.value);
    });
    return sentiments;
  }

}

let selected_sort_by_option = {

  get() {
    return $('#sort_by option:selected').val();
  }

}

