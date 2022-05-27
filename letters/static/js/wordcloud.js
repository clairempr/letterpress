jQuery(document).ready(function ($) {
    $("#search_button").click(function () {
        get_wordcloud();
    });

    get_wordcloud();
});

function get_wordcloud() {
    var inital_filter_values = filter_values.get();
    $('#message').text("");
    $('#wordcloud').attr("src", "");

    $.ajax({
        type: "GET",
        dataType: "json",
        data: {
            sources: inital_filter_values.sources,
            writers: inital_filter_values.writers,
            start_date: inital_filter_values.start_date,
            end_date: inital_filter_values.end_date,
            search_text: inital_filter_values.search_text,
        },
        url: "/wordcloud_image.png",
        success: function (result) {
            // If there was an error, redirect to error page
            if (result.redirect_url){
                window.location.href = result.redirect_url;
            }
            if (result.wc.length == 0) {
                $('#message').text("No words found");
            }
            else {
                $('#wordcloud').attr("src", "data:image/jpg;base64," + result.wc);
            }
        }
    });

    }
