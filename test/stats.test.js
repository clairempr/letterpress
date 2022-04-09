/* global QUnit, stats */
'use strict';

QUnit.module("stats", function (hooks) {
  hooks.beforeEach(function (assert) {
    $('<div id="chart"></div>').appendTo('#qunit-fixture');
    $('<div id="stats"></div>').appendTo('#qunit-fixture');
  });

  // All tests need to be skipped for now, because of issues with calling filter_values.get()
  // which is defined in letterpress.js

  QUnit.test.skip('get_stats Ajax success', function (assert) {
  });

  QUnit.test.skip('get_stats Ajax failure', function (assert) {
  });

});