// CHIRPS v3 daily (rnl) over northern Benin, one GeoTIFF per year.
//
// Paste into the Earth Engine code editor (code.earthengine.google.com) and
// run; start each task from the Tasks tab. Files land in Google Drive,
// folder "agritech". One file per year: a single 1981-2025 export would
// stack about 16,400 bands and fail. See docs/data/chirps.md.

// Zone A with a small margin, so that border communes keep all their pixels.
var zone = ee.Geometry.Rectangle([0.8, 8.6, 3.8, 12.5], 'EPSG:4326', false);
var FIRST_YEAR = 1981;
var LAST_YEAR = 2025;

// DAILY_RNL starts in 1981; DAILY_SAT only in 1998.
var chirps = ee.ImageCollection('UCSB-CHC/CHIRPS/V3/DAILY_RNL').filterBounds(zone);

for (var year = FIRST_YEAR; year <= LAST_YEAR; year++) {
  var days = chirps.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year + 1, 1, 1));
  // One band per day, named YYYYMMDD: the Python reader takes the date from it.
  var image = days.toBands().rename(days.aggregate_array('system:index'));
  Export.image.toDrive({
    image: image,
    description: 'chirps_v3_benin_' + year,
    folder: 'agritech',
    fileNamePrefix: 'chirps_v3_benin_' + year,
    region: zone,
    scale: 5566, // 0.05 degree at the equator
    crs: 'EPSG:4326',
    fileFormat: 'GeoTIFF',
    maxPixels: 1e13,
    skipEmptyTiles: true
  });
}
