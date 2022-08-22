<?php
function escapeJsonString($value) { # list from www.json.org: (\b backspace, \f formfeed)
  $escapers = array("\\", "/", "\"", "\n", "\r", "\t", "\x08", "\x0c");
  $replacements = array("\\\\", "\\/", "\\\"", "\\n", "\\r", "\\t", "\\f", "\\b");
  $result = str_replace($escapers, $replacements, $value);
  return $result;
}
# Connect to PostgreSQL database
$servername = "localhost:5432";
$password = "xxxxx";
$username = "user";
$dbname = "db_osm_routing";

// Create connection
$conn = pg_connect("host=localhost port=5432 dbname=db_osm_routing user=user password=xxxxx");
if (!$conn) {
    echo "Not connected : ";
    exit;
}

# Build SQL SELECT statement and return the geometry as a GeoJSON element in EPSG: 4326
#$sql = "SELECT osm_id, highway, st_asgeojson(ST_Transform(way,4326)) AS geojson FROM planet_osm_line WHERE ST_Within(ST_Transform(way,4326), ST_Buffer((SELECT ST_Transform(wkb_geometry,4326) FROM tracks WHERE ogc_fid = 1), 100,'endcap=round join=round')) LIMIT 10";
#$sql = "SELECT id, tags, st_asgeojson(ST_Transform(geom_linestring,4326)) AS geojson FROM otrouting_ways WHERE ST_Within(ST_Transform(geom_linestring,4326),(SELECT ST_GeomFromWKB(ST_Buffer((SELECT wkb_geometry FROM tracks WHERE ogc_fid = 1),0.00003))))";
$sql = "SELECT id, tags, st_asgeojson(ST_Transform(geom_linestring,4326)) AS geojson FROM otrouting_ways WHERE gpx_weight != 0";
//echo $sql;

# Try query or error
$rs = pg_query($conn, $sql);
if (!$rs) {
    echo "An SQL error occured.\n";
    exit;
}

# Build GeoJSON
$output    = '';
$rowOutput = '';

while ($row = pg_fetch_assoc($rs)) {
    $rowOutput = (strlen($rowOutput) > 0 ? ',' : '') . '{"type": "Feature", "geometry": ' . $row['geojson'] . ', "properties": {';
    $props = '';
    $id    = '';
    foreach ($row as $key => $val) {
        if ($key != "geojson") {
            $props .= (strlen($props) > 0 ? ',' : '') . '"' . $key . '":"' . escapeJsonString($val) . '"';
        }
        if ($key == "id") {
            $id .= ',"id":"' . escapeJsonString($val) . '"';
        }
    }

    $rowOutput .= $props . '}';
    $rowOutput .= $id;
    $rowOutput .= '}';
    $output .= $rowOutput;
}

$output = '{ "type": "FeatureCollection", "features": [ ' . $output . ' ]}';
echo $output;
?>
