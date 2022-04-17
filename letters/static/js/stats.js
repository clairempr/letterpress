jQuery(document).ready(function ($) {
    $("#search_button").click(function () {
        get_stats();
    });
});

function get_stats() {
    var inital_filter_values = filter_values.get();

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            sources: inital_filter_values.sources,
            writers: inital_filter_values.writers,
            start_date: inital_filter_values.start_date,
            end_date: inital_filter_values.end_date,
            words: inital_filter_values.words
        },
        url: "/get_stats/",
        success: function (result) {
            $('#chart').html(result.chart);
            $('#stats').html(result.stats);
        }
    });
}
