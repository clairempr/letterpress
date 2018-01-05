jQuery(document).ready(function ($) {
    $("#search_button").click(function () {
        get_wordcloud();
    });

    get_wordcloud();
});

function get_wordcloud() {
    var filter_values = get_filter_values();
    $('#message').text("");
    $('#wordcloud').attr("src", "");

    $.ajax({
        type: "GET",
        dataType: "json",
        data: {
            sources: filter_values.sources,
            writers: filter_values.writers,
            start_date: filter_values.start_date,
            end_date: filter_values.end_date,
            search_text: filter_values.search_text,
        },
        url: "/wordcloud_image.png",
        success: function (result) {
            if (result.wc.length == 0) {
                $('#message').text("No words found");
            }
            else {
                $('#wordcloud').attr("src", "data:image/jpg;base64," + result.wc);
            }
        }
    });

    }
