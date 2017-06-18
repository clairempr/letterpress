/* JavaScript for generating OpenStreetMap and features using OpenLayers 4  */

var map = {};
var EPSG3857Extent = ol.proj.get('EPSG:3857').getExtent();

function map_init(features, marker_image, plain_marker_image, popups) {
    MAX_ZOOM = 9;

    var iconStyle = create_icon_style(marker_image, '');

    var styleCache = {};
    styleCache[1] = iconStyle;

    var vectorSource = new ol.source.Vector({
        features: features
    });

    var vectorLayer = new ol.layer.Vector({
       source: vectorSource,
        style: iconStyle
    });

    var clusterSource = new ol.source.Cluster({
        distance: 10,
        source: vectorSource
    });

    var clusters = new ol.layer.Vector({
        source: clusterSource,
        style: function (feature) {
            var size = feature.get('features').length;
            var style = styleCache[size];
            if (!style) {
                style = create_icon_style(plain_marker_image, size.toString());
                styleCache[size] = style;
            }
            return style;
        }
    });

    map = new ol.Map({
        target: document.getElementById('mapdiv'),
        view: new ol.View({
            projection: 'EPSG:3857'
        }),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            // vectorLayer
            clusters
        ]
    });

    // Center and zoom map according to places shown
    var view = map.getView();
    view.fit(vectorSource.getExtent(), {size: map.getSize()});

    // Make sure map isn't zoomed in too far, if there's only one point
    if (view.getZoom() > MAX_ZOOM) {
        view.setZoom(MAX_ZOOM);
    }

    if (popups) {
        popup_init();
    }
}

function popup_init() {
    var popup_element = document.getElementById('popup');

    var popup = new ol.Overlay({
        element: popup_element,
        positioning: 'bottom-center',
        stopEvent: false,
        offset: [0, -50]
    });

    map.addOverlay(popup);

// display popup on click
    map.on('click', function (evt) {

        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function (feature) {
                return feature;
            });

        if (!feature) {
            $(popup_element).popover('hide');
            return;
        }

        // Only show popup for unclustered feature
        var cfeatures = feature.get('features');
        if (cfeatures.length == 1) {
            feature = cfeatures[0];
            var name = feature.get('name');
            $(popup_element).popover({
                'placement': 'top',
                'html': true
            });
            // Make sure content gets updated each time a new feature is clicked
            $(popup_element).attr('data-content', name);
            var coordinates = feature.getGeometry().getCoordinates();
            popup.setPosition(coordinates);
            $(popup_element).popover('show');
        }
        else {
            $(popup_element).popover('hide');
        }
    });
}

function create_feature(point, name) {
    return new ol.Feature({
        geometry: point,
        name: name
    });
}

function create_point(x, y) {
    // Define markers as "features" of the vector layer:
    var point = new ol.geom.Point([x, y]);

    // Transform from WGS 1984 projection to Spherical Mercator projection
    point.transform("EPSG:4326", "EPSG:3857");

    // Make sure point's coordinates fit within extent of the projection

    return ol.extent.containsExtent(EPSG3857Extent, point.getExtent()) ? point : 0
}

function create_icon_style(image_file, text) {
    var style = new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
            anchor: [0.5, 42],
            anchorXUnits: 'fraction',
            anchorYUnits: 'pixels',
            src: image_file
        }))
    });

    if (text) {
        var textStyle = new ol.style.Text({
            text: text,
            offsetY: -25,
            fill: new ol.style.Fill({
                color: '#fff',
            })
        });
        style.setText(textStyle);
    }

    return style;
}

