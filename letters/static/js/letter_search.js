jQuery(document).ready(function ($) {
    let last_page = 0;

    // If coming back to this page after a letter view, show the search results again
    if (history.state) {
        search_results.restore(history.state.result, history.state.pagination);
    }

    // Enable going back and forth between pages of search results with back button
    window.addEventListener('popstate', function (event) {
        if (event.state) {
            search_results.restore(event.state.result, event.state.pagination);
        }
    }, false);

    $("#search_button").click(function () {
        alert('clicked');
        search.do_search(0);
    });
});

let search = {

    do_search(page_number) {
        active_page.clear();
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
                search_results.show(result, page_number);
                //window.location.hash = "#search_button";
            }
        });
    }

}

let search_results = {

    show(result, page_number) {
        $('#letters').html(result.letters);
        if (result.pagination) {
            pagination.set(result.pagination);
            last_page = result.pages;
            active_page.set(1);
        } else {
            active_page.set(page_number);
        }

        var stateObj = {
            result: result,
            pagination: $('#pagination-top').get(0).innerHTML
        };
        history.replaceState(stateObj, '', '?page=' + page_number);
    },

    restore(result, pagination_to_restore) {
        $('#letters').html(result.letters);
        pagination.set(pagination_to_restore);
        last_page = result.pages;
    }

}

let pagination = {

    set(pagination_to_set) {
        $('#pagination-top').html(pagination_to_set);
        $('#pagination-bottom').html(pagination_to_set);
    }

}

let active_page = {

    clear() {
        $('ul#pages.pagination').find('.active').removeClass('active');
    },

    get() {
        // Pagination at top and bottom of page. Just get the first.
        var active_page_item = $('ul#pages.pagination').find('.active').get(0);
        var the_active_page = parseInt(active_page_item.innerText);
        return the_active_page;
    },

    set(new_page) {
        $('li[name=page' + new_page + ']').addClass('active');
    }

}

let search_page = {

    next() {
        var the_active_page = active_page.get();
        if (the_active_page < last_page) {
            search.do_search(the_active_page + 1);
        }
    },

    prev() {
        var the_active_page = active_page.get();
        if (the_active_page > 1) {
            search.do_search(the_active_page - 1);
        }
    }

}
