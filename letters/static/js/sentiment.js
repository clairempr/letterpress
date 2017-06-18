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
            $('#sentiment-highlights').html(result.sentiment_highlights);
        }
    });
}

