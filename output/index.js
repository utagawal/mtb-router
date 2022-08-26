//Openlayers js configuration
var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    })
  ],
  view: new ol.View({
    projection: 'EPSG:4326',
    center: [5.1416421, 45.501295],
    zoom: 8
  })
});

//Show GPX lines on openlayers

fetch('load_osm_ways.php', {
  method: 'post',
    body: 'oui = ',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
})
.then(r => r.json())
.then(res_osm => {
  console.log(res_osm);
  var vectorSource_osm = new ol.source.Vector({
    features: (new ol.format.GeoJSON()).readFeatures(res_osm)
  });
  var vectorLayer_osm = new ol.layer.Vector({
    style: new ol.style.Style({
                fill: new ol.style.Stroke({
                    color: "#FF5733",
                }),
                stroke: new ol.style.Stroke({
                    color: "#FF5733",
                    width: 3,
                }),
            }),
    source: vectorSource_osm,
      visible: true
  });
  map.addLayer(vectorLayer_osm);
});

fetch('load_gpx.php', {
  method: 'post',
    body: 'oui = ',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
})
.then(r => r.json())
.then(res => {
  console.log(res);
  var vectorSource = new ol.source.Vector({
    features: (new ol.format.GeoJSON()).readFeatures(res)
  });
  var vectorLayer = new ol.layer.Vector({
    style: new ol.style.Style({
                fill: new ol.style.Stroke({
                    color: "#0026FF",
                }),
                stroke: new ol.style.Stroke({
                    color: "#0026FF",
                    width: 6,
                }),
            }),
    source: vectorSource,
    visible: true
  });
  map.addLayer(vectorLayer);
});
