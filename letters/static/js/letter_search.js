jQuery(document).ready(function ($) {
    var last_page = 0;

    // If coming back to this page after a letter view, show the search results again
    if (history.state) {
        restore_search_results(history.state.result, history.state.pagination);
    }

    // Enable going back and forth between pages of search results with back button
    window.addEventListener('popstate', function (event) {
        if (event.state) {
            restore_search_results(event.state.result, event.state.pagination);
        }
    }, false);

    $("#search_button").click(function () {
        do_search(0);
    });
});

function do_search(page_number) {
    clear_active_page();
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
            sentiments: filter_values.sentiments,
            sort_by: filter_values.sort_by,
            page_number: page_number,
        },
        url: "/search/",
        success: function (result) {
            show_search_results(result, page_number);
        }
    });
}

function show_search_results(result, page_number) {
    $('#letters').html(result.letters);
    if (result.pagination) {
        set_pagination(result.pagination);
        last_page = result.pages;
        set_active_page(1);
    }
    else {
        set_active_page(page_number);
    }

    var stateObj = {
        result: result,
        pagination: $('#pagination-top').get(0).innerHTML
    };
    history.replaceState(stateObj, '', '?page=' + page_number);
}

function restore_search_results(result, pagination) {
    $('#letters').html(result.letters);
    set_pagination(pagination);
    last_page = result.pages;
}

function set_pagination(pagination) {
    $('#pagination-top').html(pagination);
    $('#pagination-bottom').html(pagination);
}

function set_active_page(new_page) {
    $('li[name=page' + new_page + ']').addClass('active');
}

function clear_active_page() {
    $('ul#pages.pagination').find('.active').removeClass('active');
}

function get_active_page() {
    // Pagination at top and bottom of page. Just get the first.
    var active_page_item = $('ul#pages.pagination').find('.active').get(0);
    var active_page = parseInt(active_page_item.innerText);
    return active_page;
}

function search_next_page() {
    var active_page = get_active_page();
    if (active_page < last_page) {
        do_search(active_page + 1);
    }
}

function search_prev_page() {
    var active_page = get_active_page();
    if (active_page > 1) {
        do_search(active_page - 1);
    }
}

