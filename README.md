## Letterpress ##
![Screenshot](screenshots/home.png) 
*Claire Pritchard*  
*April 2017*   

Letterpress is a Django web application for the management of transcriptions and images of letters and related documents. 
I originally created it to help manage my transcriptions of 19th-century correspondence which I was using as input for 
natural language processing experiments. 

The name comes from an early office technology which people used to duplicate documents and store them in a 
[letterpress copybook](http://www2.archivists.org/glossary/terms/l/letterpress-copybook).

 ![Letter](screenshots/letter.png)

#### Features ####

 - Highly customized Django Admin
 - Full-text searching with Elasticsearch
 ![Fuzzy text search](screenshots/text_search.png)
 - SQLite database
 - Place mapping with OpenStreetMap and OpenLayers 4
 ![Map](screenshots/map_with_popup.png)
 - Export to text files
 - Word frequency statistics by month, with Bokeh charts
 ![Charts](screenshots/charts.png)
 - Word clouds for writers, date ranges, etc.
  ![Charts](screenshots/wordcloud_page.png)
 
#### Notes ####
 - [Elasticsearch](https://www.elastic.co/products/elasticsearch) must be installed and running.
 - Elasticsearch index can be created or updated manually with the Django management command push_to_index, otherwise updates are automatic when the model is saved.
 - Text searches are fuzzy by default. For exact match, enclose search terms in quotes.
 - See [GeoDjango](https://docs.djangoproject.com/en/1.10/ref/contrib/gis/) for information on using GIS features with Django.
 - [libspatialite](https://www.gaia-gis.it/fossil/libspatialite/index) must be installed and the location configured in Django settings.
 - [GDAL](http://www.gdal.org/index.html) must be installed. Windows binaries can be found here: http://www.gisinternals.com/release.php.
 - This application is much easier to run under Linux than under Windows. For Windows:
    - Install the GDAL core components for the appropriate version and set the GDAL_LIBRARY_PATH (path to GDAL dll) in Django settings.
    - Add the GDAL directory (containing GDAL dll) to your Windows PATH.
    - Add a System variable with name GDAL_DATA and value of the path to the gdal-data folder containing gcs.csv, etc.
    - If you get the error "no such module: rtree" or "Error transforming geometry...(OGR failure.)", try replacing sqlite3.dll in system python directory with another sqlite3.dll, like one from [OSGeo4W](https://trac.osgeo.org/osgeo4w/).

#### Credits ####
Photograph of copy press from [Letterpress Commons](https://letterpresscommons.com), 
map marker from [Maps Icons Collection](https://mapicons.mapsmarker.com), other images public domain.
