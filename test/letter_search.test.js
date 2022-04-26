/* global QUnit, letter_search */
'use strict';

QUnit.module("letter_search", function (hooks) {
  hooks.before(function (assert) {
    last_page = 0;
  });

  hooks.beforeEach(function (assert) {
    // Search results will get put in "letters" div
    $('<div id="pagination-top"></div>').appendTo('#qunit-fixture');
    $('<div id="letters"></div>').appendTo('#qunit-fixture');
    $('<div id="pagination-bottom"></div>').appendTo('#qunit-fixture');

    this.active_page = 3;
  });

  hooks.afterEach(function (assert) {
    sinon.restore();
  });

  QUnit.module('pagination');

  QUnit.test('set', function (assert) {
    const pagination_html = "This is the pagination html";
    pagination.set(pagination_html);

    assert.equal($('#pagination-top').html(), pagination_html, "Element with id pagination-top has pagination html set");
    assert.equal($('#pagination-bottom').html(), pagination_html, "Element with id pagination-bottom has pagination html set");
  });

  QUnit.module('active page');

  QUnit.test('clear', function (assert) {
    $('<ul id="pages" class="pagination"><li class="active">' + this.active_page + '</li></ul>').appendTo('#qunit-fixture');

    active_page.clear();

    assert.notOk($('ul#pages.pagination li').hasClass("active"), "Page list item has had 'active' class removed");
  });

  QUnit.test('get', function (assert) {
    // Pagination is at the top and bottom of the page
    // get_active_page() is supposed to get the first

    // Append top pagination to qunit-fixture
    $('<ul id="pages" class="pagination"><li>1</li><li class="active">2</li></ul>').appendTo('#qunit-fixture');
    // Append bottom pagination with different active page to qunit-fixture
    $('<ul id="pages" class="pagination"><li class="active">1</li></ul>').appendTo('#qunit-fixture');

    let the_active_page = active_page.get();

    assert.equal(the_active_page, 2, "Active page is first one with 'active' class");
  });

  QUnit.test('set', function (assert) {
    const new_page = 3;
    active_page.set(new_page);
    assert.notOk($("li[name=page" + new_page + "]").hasClass("active"), "Current page list item has had 'active' class set");
  });

  QUnit.module('search');

  QUnit.test('do_search', function (assert) {
    // search.do_search() should call active_page.clear() and make an ajax call
    // If ajax call not successful, search_results.show() shouldn't be called
    let fake_clear_active_page = sinon.replace(active_page, "clear", sinon.fake());
    let fake_ajax = sinon.replace(jQuery, "ajax", sinon.fake());
    let fake_show_search_results = sinon.replace(search_results, "show", sinon.fake());

    letter_search.do_search(
      fake_clear_active_page,
      fake_ajax,
      fake_show_search_results
    );

    assert.ok(active_page.clear.called, "active_page.clear() has been called");
    assert.ok(jQuery.ajax.called, "An ajax call has been made");
    assert.notOk(search_results.show.called, "search_results.show() has not been called");

    sinon.restore();

    // If ajax call was successful, search_results.show() should be called
    const letters = "These are the letters";
    const pages = "These are the pages";
    const data = {
      letters: letters,
      pages: pages
    }
    sinon.stub(jQuery, "ajax").yieldsTo("success", data);
    fake_show_search_results = sinon.replace(search_results, "show", sinon.fake());

    letter_search.do_search(
      fake_show_search_results
    );

    assert.ok(search_results.show.called, "search_results.show() has been called");

    sinon.restore();
  });

  QUnit.module('search page', {
    beforeEach: function () {
      $('<ul id="pages" class="pagination"><li class="active">' + this.active_page + '</li></ul>').appendTo('#qunit-fixture');
    },
  });

  QUnit.test('next', function (assert) {
    let fake_get_active_page = sinon.replace(active_page, "get", sinon.fake.returns(2));
    let fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());
    // if the_active_page.get() >= last_page, search.do_search() shouldn't get called
    last_page = 1;

    search_page.next(fake_get_active_page, fake_do_search);

    assert.ok(active_page.get.called, "active_page.get() has been called");
    assert.notOk(letter_search.do_search.called, "letter_search.do_search() hasn't been called");

    sinon.restore();

    // if the_active_page.get() >= last_page, letter_search.do_search() shouldn't get called
    last_page = 2;

    sinon.replace(active_page, "get", sinon.fake.returns(2));
    fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());

    search_page.next(fake_do_search);

    assert.notOk(letter_search.do_search.called, "letter_search.do_search() hasn't been called");

    sinon.restore();

    // if the_active_page.get() < last_page, letter_search.do_search() should get called
    last_page = 3;

    sinon.replace(active_page, "get", sinon.fake.returns(2));
    fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());

    search_page.next(fake_do_search);

    assert.ok(letter_search.do_search.called, "letter_search.do_search() has been called");

    sinon.restore();
  });

  QUnit.test('prev', function (assert) {
    let fake_get_active_page = sinon.replace(active_page, "get", sinon.fake.returns(1));
    let fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());
    last_page = 0;

    search_page.prev(fake_get_active_page, fake_do_search);

    assert.ok(active_page.get.called, "active_page.get() has been called");
    // if the_active_page.get() <= 1, letter_search.do_search() shouldn't get called
    assert.notOk(letter_search.do_search.called, "letter_search.do_search() has been called");

    sinon.restore();

    // if the_active_page.get() <= 1, letter_search.do_search() shouldn't get called
    last_page = 1;

    sinon.replace(active_page, "get", sinon.fake.returns(1));
    fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());

    search_page.prev(fake_get_active_page, fake_do_search);

    assert.notOk(letter_search.do_search.called, "letter_search.do_search() has been called");

    sinon.restore();

    // if active_page.get() > 1, letter_search.do_search() should get called
    last_page = 1;

    sinon.replace(active_page, "get", sinon.fake.returns(2));
    fake_do_search = sinon.replace(letter_search, "do_search", sinon.fake());

    search_page.prev(fake_get_active_page, fake_do_search);

    assert.ok(letter_search.do_search.called, "letter_search.do_search() has been called");

    sinon.restore();
  });

  QUnit.module('search results', {
    before: function () {
      this.letters = "These are the letters";
      this.pages = 5;
      this.result = {
        letters: this.letters,
        pages: this.pages
      };
    },
  });

  QUnit.test('restore', function (assert) {
    this.pagination = "This is the pagination";

    let fake_set_pagination = sinon.replace(pagination, "set", sinon.fake());

    search_results.restore(this.result, this.pagination, fake_set_pagination);

    assert.equal($('#letters').html(), this.letters, "Element with id letters has letters html set");
    assert.ok(pagination.set.called, "pagination.set() has been called");

    sinon.restore();
  });

  QUnit.test('show', function (assert) {
    let fake_set_pagination = sinon.replace(pagination, "set", sinon.fake());
    let fake_set_active_page = sinon.replace(active_page, "set", sinon.fake());

    sinon.replace(history, "replaceState", sinon.fake());

    search_results.show(this.result, 3, fake_set_pagination, fake_set_active_page);

    assert.equal($('#letters').html(), this.letters, "Element with id letters has letters html set");
    assert.ok(history.replaceState.called, "history.replaceState() has been called");
    assert.ok(active_page.set.called, "active_page.set() has been called");

    // If result.pagination isn't filled, pagination.set() shouldn't get called
    assert.notOk(pagination.set.called, "pagination.set() hasn't been called");

    sinon.restore();

    // If result.pagination is filled, pagination.set() should get called
    this.result.pagination = "This is the pagination";

    fake_set_pagination = sinon.replace(pagination, "set", sinon.fake());
    fake_set_active_page = sinon.replace(active_page, "set", sinon.fake());

    search_results.show(this.result, 3, fake_set_pagination, fake_set_active_page);

    assert.ok(pagination.set.called, "pagination.set() has been called");
    assert.ok(active_page.set.called, "active_page.set() has been called");

    sinon.restore();
  });

});
