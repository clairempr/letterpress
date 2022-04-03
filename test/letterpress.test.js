/* global QUnit, letterpress */
'use strict';

QUnit.module("letterpress", function (hooks) {
  hooks.beforeEach(function (assert) {
    // Search results will get put in "letters" div
    $('<div id="pagination-top"></div>').appendTo('#qunit-fixture');
    $('<div id="letters"></div>').appendTo('#qunit-fixture');
    $('<div id="pagination-bottom"></div>').appendTo('#qunit-fixture');

    this.active_page = 3;
  });

  QUnit.module('csrf');

  QUnit.test('csrfSafeMethod', function (assert) {
    assert.ok(csrfSafeMethod("GET"), "csrfSafeMethod(GET) returns true");
    assert.ok(csrfSafeMethod("HEAD"), "csrfSafeMethod(HEAD) returns true");
    assert.ok(csrfSafeMethod("OPTIONS"), "csrfSafeMethod(OPTIONS) returns true");
    assert.ok(csrfSafeMethod("TRACE"), "csrfSafeMethod(TRACE) returns true");
    assert.notOk(csrfSafeMethod("POST"), "csrfSafeMethod(POST) returns false");
  });

  QUnit.test('jQuery.ajaxSetup.beforeSend', function (assert) {
    let xhr = $.ajax();

    // If it's not a CSRF safe method and crossDomain is false, setRequestHeader() should get called
    let settings = {'type': 'POST'};
    $.ajaxSetup().crossDomain = false;

    let fake_xhr_setRequestHeader = sinon.replace(xhr, "setRequestHeader", sinon.fake());

    $.ajaxSetup().beforeSend(xhr, settings, fake_xhr_setRequestHeader);

    assert.ok(xhr.setRequestHeader.called, "xhr.setRequestHeader() has been called");

    sinon.restore();

    // If it's a CSRF safe method, setRequestHeader() shouldn't get called
    settings = {'type': 'GET'};
    $.ajaxSetup().crossDomain = false;

    fake_xhr_setRequestHeader = sinon.replace(xhr, "setRequestHeader", sinon.fake());

    $.ajaxSetup().beforeSend(xhr, settings, fake_xhr_setRequestHeader);

    assert.notOk(xhr.setRequestHeader.called, "xhr.setRequestHeader() hasn't been called");

    sinon.restore();

    // If crossDomain is true, setRequestHeader() shouldn't get called
    settings = {'type': 'POST'};
    $.ajaxSetup().crossDomain = true;

    fake_xhr_setRequestHeader = sinon.replace(xhr, "setRequestHeader", sinon.fake());

    $.ajaxSetup().beforeSend(xhr, settings, fake_xhr_setRequestHeader);

    assert.notOk(xhr.setRequestHeader.called, "xhr.setRequestHeader() hasn't been called");

    sinon.restore();
  });

  QUnit.module('filter values');

  QUnit.test('get sources and writers', function (assert) {
    $('<div id="sources" class="checkbox">' +
      '<input type="checkbox" value="source 1" checked>' +
      '<input type="checkbox" value="source 2">' +
      '<input type="checkbox" value="source 3" checked></div>').appendTo('#qunit-fixture');
    $('<div id="writers" class="checkbox">' +
      '<input type="checkbox" value="writer 1" checked>' +
      '<input type="checkbox" value="writer 2">' +
      '<input type="checkbox" value="writer 3" checked></div>').appendTo('#qunit-fixture');

    let the_filter_values = filter_values.get();

    // sources should be values of checked checkboxes under #sources
    assert.ok(the_filter_values.sources.includes("source 1"), "sources includes checked source");
    assert.notOk(the_filter_values.sources.includes("source 2"), "sources doesn't include unchecked source");
    assert.ok(the_filter_values.sources.includes("source 3"), "sources includes checked source");

    // writers should be values of checked checkboxes under #writers
    assert.ok(the_filter_values.writers.includes("writer 1"), "writers includes checked writer");
    assert.notOk(the_filter_values.writers.includes("writer 2"), "writers doesn't include unchecked writer");
    assert.ok(the_filter_values.writers.includes("writer 3"), "writers includes checked writer");
  });

  QUnit.test('get start and end dates', function (assert) {
    $('<input type="text" id="start_date" value="">').appendTo('#qunit-fixture');
    $('<input type="text" id="end_date" value="">').appendTo('#qunit-fixture');

    const dates = {
      "start_dates": ["1849-02-01", "1849", ""],
      "end_dates": ["1904-12-19", "1904", ""]
    }

    for (let i = 0; i < dates["start_dates"].length; i++) {
      let start_date = dates["start_dates"][i]
      let end_date = dates["end_dates"][i]

      $("#start_date").val(start_date);
      $("#end_date").val(end_date);

      let the_filter_values = filter_values.get();

      assert.equal(the_filter_values.start_date, start_date, "start_date is equal to start_date value '" + start_date + "'");
      assert.equal(the_filter_values.end_date, end_date, "end_date is equal to end_date value '" + start_date + "'");
    }

  });

  QUnit.test('get search text', function (assert) {
    $('<input type="text" id="search_text">').appendTo('#qunit-fixture');

    let search_text = "search text";
    $("#search_text").val(search_text);

    let the_filter_values = filter_values.get();

    assert.equal(the_filter_values.search_text, search_text, "search_text is equal to search_text value '" + search_text + "'");

    search_text = "";
    $("#search_text").val(search_text);

    the_filter_values = filter_values.get();

    assert.equal(the_filter_values.search_text, search_text, "search_text is equal to search_text value '" + search_text + "'");
  });

  QUnit.test('get sentiments', function (assert) {
    $('<input type="text" id="word1"><input type="text" id="word2">').appendTo('#qunit-fixture');

    // both words filled
    let word1 = "&";
    let word2 = "and";

    $("#word1").val(word1);
    $("#word2").val(word2);

    let the_filter_values = filter_values.get();

    assert.ok(the_filter_values.words.includes(word1), "words includes word1 if word1 filled");
    assert.ok(the_filter_values.words.includes(word2), "words includes word2 if word2 filled");

    // word1 filled
    word1 = "&";
    word2 = "";

    $("#word1").val(word1);
    $("#word2").val(word2);

    the_filter_values = filter_values.get();

    assert.ok(the_filter_values.words.includes(word1), "words includes word1 if word1 filled");
    assert.notOk(the_filter_values.words.includes(word2), "words doesn't include empty word2");

    // word2 filled
    word1 = "";
    word2 = "and";

    $("#word1").val(word1);
    $("#word2").val(word2);

    the_filter_values = filter_values.get();

    assert.notOk(the_filter_values.words.includes(word1), "words doesn't include empty word1");
    assert.ok(the_filter_values.words.includes(word2), "words includes word2 if word2 filled");
  });

  QUnit.test('get selected sentiment', function (assert) {
    let the_selected_sentiments = "selected sentiments";

    let fake_get_selected_sentiment = sinon.replace(selected_sentiments, "get", sinon.fake.returns(the_selected_sentiments));

    let the_filter_values = filter_values.get();

    assert.equal(the_filter_values.sentiments, the_selected_sentiments, "sentiments is equal to selected_sentiments.get()");

    sinon.restore();
  });

  QUnit.test('get selected sort by option', function (assert) {
    let the_selected_sort_by_option = "selected sort by option";

    let fake_get_selected_sort_by_option = sinon.replace(selected_sort_by_option, "get", sinon.fake.returns(the_selected_sort_by_option));

    let the_filter_values = filter_values.get();

    assert.equal(the_filter_values.sort_by, the_selected_sort_by_option, "sort by option is equal to selected_sort_by_option.get()");
  });

  QUnit.module('selected sentiments');

  QUnit.test('get', function (assert) {
    $('<div id="sentiments" class="checkbox">' +
      '<input type="checkbox" value="sentiment 1" checked>' +
      '<input type="checkbox" value="sentiment 2">' +
      '<input type="checkbox" value="sentiment 3" checked></div>').appendTo('#qunit-fixture');

    let the_filter_values = filter_values.get();

    // sentiments should be values of checked checkboxes under #sources
    assert.ok(the_filter_values.sentiments.includes("sentiment 1"), "sentiments includes checked sentiment");
    assert.notOk(the_filter_values.sentiments.includes("sentiment 2"), "sentiments doesn't include unchecked sentiment");
    assert.ok(the_filter_values.sentiments.includes("sentiment 3"), "sentiments includes checked sentiment");

     sinon.restore();
  });

  QUnit.module('selected sort by option');

  QUnit.test('get', function (assert) {
    $('<div id="sort_by" class="checkbox">' +
      '<option value="sort by 1" selected>' +
      '<option value="sort by 2">' +
      '<option value="sort by 3"></div>').appendTo('#qunit-fixture');

    let the_filter_values = filter_values.get();

    // sentiments should be values of checked checkboxes under #sources
    assert.ok(the_filter_values.sort_by.includes("sort by 1"), "sort_by includes selected option");
    assert.notOk(the_filter_values.sort_by.includes("sort by 2"), "sort_by doesn't include unselected option");
    assert.notOk(the_filter_values.sort_by.includes("sort by 3"), "sort_by doesn't include unselected option");

     sinon.restore();
  });

});
