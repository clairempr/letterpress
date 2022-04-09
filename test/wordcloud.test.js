/* global QUnit, wordcloud */
'use strict';

QUnit.module("wordcloud", function (hooks) {
  hooks.beforeEach(function (assert) {
    $('<div id="message"></div>').appendTo('#qunit-fixture');
    $('<div id="wordcloud"></div>').appendTo('#qunit-fixture');
  });

  // All tests need to be skipped for now, because of issues with calling filter_values.get()
  // which is defined in letterpress.js

  QUnit.test.skip('get_wordcloud Ajax success', function (assert) {
  });

  QUnit.test.skip('get_wordcloud Ajax failure', function (assert) {
  });

});