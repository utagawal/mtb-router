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
$sql = "SELECT ogc_fid,name,st_asgeojson(ST_Transform(wkb_geometry,4326)) AS geojson FROM tracks";
#$sql = "SELECT ogc_fid,name,st_asgeojson(ST_Transform(wkb_geometry,4326)) AS geojson FROM tracks LIMIT 500";
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
