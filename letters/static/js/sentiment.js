function do_text_sentiment(sentiments) {
    var text = $('#text').val();

    $.ajax({
        type: "POST",
        dataType: "json",
        data: {
            text: text,
            sentiments: sentiments,
        },
        url: "/get_text_sentiment/",
        success: function(result){
            // If there was an error, redirect to error page
            if (result.redirect_url){
                window.location.href = result.redirect_url;
            }
            $('#sentiment-results').html(result.sentiments);
        }
    });
}

