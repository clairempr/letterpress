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
        // If there's an open popup, it needs to be hidden before search
        var popup_element = document.getElementById('popup');
        $(popup_element).popover('dispose');
        
        do_place_search();
    });
});

function do_place_search() {
    var inital_filter_values = filter_values.get();

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            search_text: inital_filter_values.search_text,
            sources: inital_filter_values.sources,
            writers: inital_filter_values.writers,
            start_date: inital_filter_values.start_date,
            end_date: inital_filter_values.end_date,
            page_number: 0,
        },
        url: "/places/search/",
        success: function (result) {
            // If there was an error, redirect to error page
            if (result.redirect_url){
                window.location.href = result.redirect_url;
            }
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
