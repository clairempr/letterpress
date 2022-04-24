{% load static %}
{% load l10n %}
{% block vars %}
INITIAL_ZOOM = 5;
FEATURE_ZOOM = 9;

var draw;
var map;
var vectorSource;
var wkt_format;
{% endblock %}

// Read WKT from the text field
function read_wkt(wkt) {
    var wkt = document.getElementById('{{ id }}').value;
    var feature;
    if (wkt) {
        feature = wkt_format.readFeature(wkt);
    }
    return feature;
};

// Write WKT of given feature to text field
function write_wkt(feature) {
    var wkt = 'SRID={{ srid|unlocalize }};' + wkt_format.writeFeature(feature);
    document.getElementById('{{ id }}').value = wkt;
};

function map_init() {
    wkt_format = new ol.format.WKT();

    // Read WKT from the text field
    var feature = read_wkt();
    if (feature) {
        vectorSource = new ol.source.Vector({
            features: [feature]
        });
    }
    else {
        vectorSource = new ol.source.Vector();
    }

    var iconStyle = new ol.style.Style({
        image: new ol.style.Icon(({
            anchor: [0.5, 41],
            anchorXUnits: 'fraction',
            anchorYUnits: 'pixels',
            src: '{% static "images/pen_marker.png" %}'
        }))
    });

    var vectorLayer = new ol.layer.Vector({
        source: vectorSource,
        style: iconStyle
    });

    draw = new ol.interaction.Draw({
        source: vectorSource,
        type: 'Point'
    });

    draw.on('drawstart', function (evt) {
        // Only one feature at a time allowed on map
        vectorSource.clear();
    });

    draw.on('drawend', function (evt) {
        // Get coordinates of point just added
        write_wkt(evt.feature);
    });

    {% block map_creation %}
    map = new ol.Map({
        view: new ol.View({
            center: [-8625754, 4685745],
            zoom: INITIAL_ZOOM,
            projection: 'EPSG:3857'
        }),
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            vectorLayer
        ],
        target: '{{ id }}_map',
        interactions: ol.interaction.defaults().extend([draw]),
    });

    // Center map according to place shown
    if (feature) {
        var view = map.getView();
        view.fit(vectorSource.getExtent());

        // Make sure map isn't zoomed in too far
        view.setZoom(FEATURE_ZOOM);
    }

    // Use ol3-geocoder to search for place names in the map
    var geocoder = new Geocoder('nominatim', {
        provider: 'osm',
        autoComplete: true,
        lang: 'en-US',
        placeholder: 'Search for ...',
        targetType: 'glass-button',
        limit: 8,
        keepOpen: false,
        preventDefault : true // don't automatically place feature on map
    });
    map.addControl(geocoder);

    geocoder.on('addresschosen', function (evt) {
        var feature = evt.feature,
            coord = evt.coordinate,
            address = evt.address;
        // Center and zoom in to chosen address
        var view = map.getView();
        view.setCenter(coord);
        view.setZoom(FEATURE_ZOOM);
    });
    {% endblock %}
};