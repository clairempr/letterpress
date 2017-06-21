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

function get_filter_values() {
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

    var sentiments = get_selected_sentiments();

    return {
        sources: sources,
        writers: writers,
        sentiments: sentiments,
        start_date: start_date,
        end_date: end_date,
        search_text: search_text,
        words: words
    }
}

function get_selected_sentiments() {
    var sentiments = [];
    $('#sentiments input:checked').each(function () {
        sentiments.push(this.value);
    });
    return sentiments;
}

var active_page = 0;
var last_page = 0;

function do_search(page_number) {
    var filter_values = get_filter_values();

    if (active_page != 0) {
         clear_active_page(active_page);
    }

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            search_text: filter_values.search_text,
            sources: filter_values.sources,
            writers: filter_values.writers,
            start_date: filter_values.start_date,
            end_date: filter_values.end_date,
            sentiments: filter_values.sentiments,
            page_number: page_number,
        },
        url: "/search/",
        success: function(result){
            $('#letters').html(result.letters);
            if (result.pagination){
                $('#pagination-top').html(result.pagination);
                $('#pagination-bottom').html(result.pagination);
                last_page = result.pages;
                set_active_page(1);
            }
            else {
                set_active_page(page_number);
            }
        }
    });
}

function set_active_page(new_page) {
    $('li[name=page' + new_page + ']').addClass('active');
    active_page = new_page;
}

function clear_active_page(active_page) {
    $('li[name=page' + active_page + ']').removeClass('active');
}

function search_next_page() {
    if (active_page < last_page) {
        do_search(active_page + 1);
    }
}

function search_prev_page() {
    if (active_page > 1) {
        do_search(active_page - 1);
    }
}

function do_place_search() {
    var filter_values = get_filter_values();

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            search_text: filter_values.search_text,
            sources: filter_values.sources,
            writers: filter_values.writers,
            start_date: filter_values.start_date,
            end_date: filter_values.end_date,
            page_number: 0,
        },
        url: "/search_places/",
        success: function (result) {
            $('#mapdiv').html(result.map);
        }
    });
}

function get_stats() {
    var filter_values = get_filter_values();

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            sources: filter_values.sources,
            writers: filter_values.writers,
            start_date: filter_values.start_date,
            end_date: filter_values.end_date,
            words: filter_values.words
        },
        url: "/get_stats/",
        success: function (result) {
            $('#chart').html(result.chart);
            $('#stats').html(result.stats);
        }
    });
}

