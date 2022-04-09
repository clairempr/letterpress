/* global QUnit, place_search */
'use strict';

QUnit.module("place_search", function (hooks) {
  hooks.before(function (assert) {
    $('<div id="mapdiv"></div>').appendTo('#qunit-fixture');
  });

  QUnit.module('show map');

  QUnit.test('show_map', function (assert) {
    let fake_history_replaceState = sinon.replace(history, "replaceState", sinon.fake());
    let map = "the map";

    show_map(map);

    assert.equal($('#mapdiv').html(), map, "Map has been placed in #mapdiv");
    assert.ok(fake_history_replaceState.called, "history.replaceState has been called");
  });

});