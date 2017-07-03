jQuery(document).ready(function ($) {
    $("#search_button").click(function () {
        get_stats();
    });
});

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
