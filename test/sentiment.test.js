/* global QUnit, sentiment */
'use strict';

QUnit.module("sentiment", function (hooks) {
  hooks.before(function (assert) {
    this.sentiments = "sentiments";
  });

  hooks.beforeEach(function (assert) {
    $('<div id="text"></div>').appendTo('#qunit-fixture');
    $('<div id="sentiment-results"></div>').appendTo('#qunit-fixture');
  });

  QUnit.test('do_text_sentiment Ajax success', function (assert) {
    // do_text_sentiment() should make an ajax call
    // If ajax call is successful, the result should end up in $('#sentiment-results')
    let data = {
      text: "text",
      sentiments: this.sentiments
    }
    let result = {
      sentiments: "Result sentiments"
    };
    let fake_ajax = sinon.stub(jQuery, "ajax").yieldsTo("success", result);

    do_text_sentiment(this.sentiments);

    assert.ok(fake_ajax.called, "do_text_sentiment() has made an Ajax call");
    assert.equal($('#sentiment-results').html(), result.sentiments, "Element with id sentiment-results has result.sentiments in html");

    sinon.restore();
  });

  QUnit.test('do_text_sentiment Ajax failure', function (assert) {
    // do_text_sentiment() should make an ajax call
    // If ajax call isn't successful, $('#sentiment-results').html should be empty
    let fake_ajax = sinon.replace(jQuery, "ajax", sinon.fake());

    do_text_sentiment(this.sentiments);

    assert.ok(fake_ajax.called, "do_text_sentiment() has made an Ajax call");
    assert.equal($('#sentiment-results').html(), "", "Element with id sentiment-results doesn't have result html set");

    sinon.restore();
  });

});
