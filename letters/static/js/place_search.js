jQuery(document).ready(function ($) {
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
            $('#mapdiv').html(result.map);
        }
    });
}
