jQuery(document).ready(function ($) {
    // If coming back to this page after a letter view, show the search results again
    if (history.state) {
        show_map(history.state.map);
    }

    // Enable going back and forth between pages of search results with back button
    window.addEventListener('popstate', function (event) {
        if (event.state) {
            show_map(event.state.map);
        }
    }, false);

    $("#search_button").click(function () {
        do_place_search();
    });
});

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
            show_map(result.map)
        }
    });
}

function show_map(map) {
    $('#mapdiv').html(map);

    var stateObj = {
        map: map
    };
    history.replaceState(stateObj, '', '');
}
