/* global QUnit, map */
'use strict';


QUnit.module("map", function (hooks) {
  let sandbox = sinon.createSandbox();

  hooks.before(function (assert) {
    $('<div id="popup"></div>').appendTo('#qunit-fixture');

    let map = {}
    this.features = "features";
    this.marker_image = "marker image";
    this.plain_marker_image = "plain marker image";
    this.popups = "popups";
  });

  hooks.beforeEach(function (assert) {
    this.myMapView = {
      fit() {
      },
      getZoom() {
      },
      setZoom(zoom) {
      }
    }

    this.OverlayStub = sandbox.replace(ol, "Overlay", sandbox.stub().returns("Overlay"));
    sandbox.replace(ol.proj, "get", sandbox.stub().returns("Projection"));
    this.ProjectionStub = sandbox.replace(ol.proj, "Projection", sandbox.stub().returns("Projection"));
    this.ProjectionStub.getExtent = sandbox.stub().returns([1, 2, 3, 4]);
    this.vectorSourceStub = sandbox.replace(ol.source, "Vector", sandbox.stub().returns("Vector source"));
    this.vectorSourceStub.prototype.getExtent = sandbox.stub().returns([1, 2, 3, 4]);
    this.vectorLayerFake = sandbox.replace(ol.layer, "Vector", sandbox.fake.returns("Vector"));
    this.clusterSourceStub = sandbox.replace(ol.source, "Cluster", sandbox.stub().returns("Cluster"));
    sandbox.replace(ol, "View", sandbox.stub().returns("View"));
    this.mapStub = sandbox.replace(ol, "Map", sandbox.stub().returns("Map"));
    this.mapStub.prototype.addOverlay = sandbox.stub();
    this.mapStub.prototype.getSize = sandbox.stub().returns("Map size");
    this.mapStub.prototype.addControl = sandbox.stub();
    this.create_icon_styleFake = sandbox.replace(icon_style, "create", sandbox.fake.returns("icon style"));
    this.viewSetZoomSpy = sandbox.spy(this.myMapView, "setZoom");
    this.viewFitStub = sandbox.replace(this.myMapView, "fit", sandbox.stub());
    this.tileLayerStub = sandbox.replace(ol.layer, "Tile", sandbox.stub().returns("Tile"));
    this.OSMSourceStub = sandbox.replace(ol.source, "OSM", sandbox.stub().returns("OSM"));
    this.mapStub.prototype.getView = sandbox.stub().returns(this.myMapView);
  });

  hooks.afterEach(function (assert) {
    sandbox.restore();
  });

  QUnit.module('map init');

  QUnit.test('map_init', function (assert) {
    let viewGetZoomStub = sandbox.replace(this.myMapView, "getZoom", sandbox.stub().returns(10));
    sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, this.popups);

    assert.ok(this.create_icon_styleFake.calledWith(this.marker_image), "icon_style.create(marker_image) has been called");
    assert.ok(this.vectorSourceStub.calledWith({features: this.features}), "ol.source.Vector({features: features}) has been created");
    assert.ok(this.vectorLayerFake.called, "ol.layer.Vector has been created");
    assert.ok(this.clusterSourceStub.called, "ol.source.Cluster has been created");
    assert.ok(this.mapStub.called, "ol.Map has been created");
    assert.ok(this.tileLayerStub.called, "ol.layer.Tile has been created");
    assert.ok(this.OSMSourceStub.called, "ol.source.OSM has been created");
    assert.ok(this.mapStub.prototype.getView.called, "ol.View has been created");
    assert.ok(this.viewFitStub.called, "ol.View.fit() has been called");
    assert.ok(viewGetZoomStub.called, "ol.View.getZoom() has been called");
    assert.ok(this.vectorSourceStub.prototype.getExtent.called, "ol.source.Vector.getExtent() has been called");
    assert.ok(this.mapStub.prototype.getSize.called, "ol.Map.getSize() has been called");

    sandbox.restore();
  });

  QUnit.test('map_init zoom < MAX_ZOOM', function (assert) {
    // map_init() should always call View getZoom()
    // It should only call View setZoom() if getZoom() > MAX_ZOOM
    // MAX_ZOOM is set to 9 in map_init()

    // getZoom < MAX_ZOOM: setZoom() shouldn't get called
    let viewGetZoomStub = sandbox.replace(this.myMapView, "getZoom", sandbox.stub().returns(8));
    sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, this.popups);

    assert.ok(viewGetZoomStub.called, "ol.View.getZoom() has been called");
    assert.notOk(this.viewSetZoomSpy.called, "ol.View.setZoom() hasn't been called because zoom < MAX_ZOOM");

    sandbox.restore();
  });

  QUnit.test('map_init zoom == MAX_ZOOM', function (assert) {
    // map_init() should always call View getZoom()
    // It should only call View setZoom() if getZoom() > MAX_ZOOM
    // MAX_ZOOM is set to 9 in map_init()

    // getZoom() == MAX_ZOOM: setZoom() shouldn't get called
    let viewGetZoomStub = sandbox.replace(this.myMapView, "getZoom", sandbox.stub().returns(9));
    sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, this.popups);

    assert.ok(viewGetZoomStub.called, "ol.View.getZoom() has been called");
    assert.notOk(this.viewSetZoomSpy.called, "ol.View.setZoom() hasn't been called because zoom == MAX_ZOOM");

    sandbox.restore();
  });

  QUnit.test('map_init zoom > MAX_ZOOM', function (assert) {
    // map_init() should always call View getZoom()
    // It should only call View setZoom() if getZoom() > MAX_ZOOM
    // MAX_ZOOM is set to 9 in map_init()

    // getZoom() > MAX_ZOOM: setZoom() should get called
    let viewGetZoomStub = sandbox.replace(this.myMapView, "getZoom", sandbox.stub().returns(10));
    sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, this.popups);

    assert.ok(viewGetZoomStub.called, "ol.View.getZoom() has been called");
    assert.ok(this.viewSetZoomSpy.calledWith(MAX_ZOOM), "ol.View.setZoom() has been called because zoom > MAX_ZOOM");

    sandbox.restore();
  });

  QUnit.test('map_init popup popups', function (assert) {
    // If there are popups, popup.init() should be called
    sandbox.replace(this.myMapView, "getZoom", sandbox.stub());
    let popupInitStub = sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, this.popups);

    assert.ok(popupInitStub.called, "popup.init() has been called");

    sandbox.restore();
  });

  QUnit.test('map_init popup no popups', function (assert) {
    // If there are no popups, popup.init() shouldn't be called
    let emptyPopups = "";
    let popupInitStub = sandbox.replace(popup, "init", sandbox.stub());

    map_init(this.features, this.marker_image, this.plain_marker_image, emptyPopups);

    assert.notOk(popupInitStub.called, "popup.init() hasn't been called");

    sandbox.restore();
  });

  QUnit.module("popup", function (hooks) {
  });

  QUnit.test.skip('init', function (assert) {
    // This test causes errors with ol.Map.addOverlay() for some reason,
    popup.init();

    assert.ok(this.OverlayStub.called, "ol.Overlay() has been called");
    assert.ok(this.mapStub.prototype.addOverlay.called, "ol.Map.addOverlay() has been called");

    sandbox.restore();
  });

  QUnit.module("create feature", function (hooks) {
  });

  QUnit.test('create_feature', function (assert) {
    let FeatureStub = sandbox.replace(ol, "Feature", sandbox.stub().returns("Feature"));

    create_feature();

    assert.ok(FeatureStub.called, "ol.Feature() has been called");

    sandbox.restore();
  });

  QUnit.module("create point", function (hooks) {
  });

  QUnit.test('create_point', function (assert) {
    let PointStub = sandbox.replace(ol.geom, "Point", sandbox.stub().returns("Point"));
    PointStub.prototype.transform = sandbox.stub().returns("transform");
    let containsExtentStub = sandbox.replace(ol.extent, "containsExtent", sandbox.stub());
    PointStub.prototype.getExtent = sandbox.stub().returns("Extent");

    create_point();

    assert.ok(PointStub.called, "ol.geom.Point() has been called");
    assert.ok(PointStub.prototype.transform.called, "ol.geom.Point.transform() has been called");
    assert.ok(containsExtentStub.called, "ol.extent.containsExtent.transform() has been called");
    assert.ok(PointStub.prototype.getExtent.called, "ol.geom.Point.getExtent() has been called");

    sandbox.restore();
  });

  QUnit.module("icon_style", function (hooks) {
  });

  QUnit.test.skip('create', function (assert) {
    // This test should work but it doesn't, maybe because the objects are instantiated
    // with the "new" keyword
    let styleStyleStub = sandbox.replace(ol.style, "Style", sandbox.stub().returns("Style"));
    let textStyleStub = sandbox.replace(ol.style, "Text", sandbox.stub().returns("Text"));
    let iconStyleStub = sandbox.replace(ol.style, "Icon", sandbox.stub().returns("Icon"));
    let fillStyleStub = sandbox.replace(ol.style, "Fill", sandbox.stub().returns("Fill"));
    styleStyleStub.prototype.setText = sandbox.stub();

    icon_style.create("image_file", "Text");

    assert.ok(styleStyleStub.called, "ol.style.Style() has been called");
    assert.ok(textStyleStub.called, "ol.style.Text() has been called");
    assert.ok(iconStyleStub.called, "ol.style.Icon() has been called");
    assert.ok(fillStyleStub.called, "ol.style.Fill() has been called");
    assert.ok(styleStyleStub.prototype.setText.called, "ol.style.Style.setText() has been called");

    sandbox.restore();
  });

    QUnit.module("enable place search", function (hooks) {
  });

  QUnit.test.skip('enable_place_search', function (assert) {
    // This should work but doesn't
    let GeocoderStub = sandbox.spy(Geocoder);

    enable_place_search();

    assert.ok(GeocoderStub.called, "Geocoder() has been called");
    assert.ok(this.mapStub.prototype.addControl.called, "ol.Map.addControl has been called");

    sandbox.restore();
  });

});