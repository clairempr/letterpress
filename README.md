Letterpress
===========

[![CircleCI](https://circleci.com/gh/clairempr/letterpress/tree/main.svg?style=svg)](https://circleci.com/gh/clairempr/letterpress/tree/main)
[![Coverage Status](https://coveralls.io/repos/github/clairempr/letterpress/badge.svg)](https://coveralls.io/github/clairempr/letterpress)
![Screenshot](screenshots/home.png) 
*Claire Pritchard*  
*April 2017 - Present*   

Letterpress is a [Django](https://www.djangoproject.com/) web application for the management of transcriptions and images of letters and related documents. 
I originally created it to help manage my transcriptions of 19th-century correspondence which I was using as input for 
natural language processing experiments. 

The name comes from an early office technology which people used to duplicate documents and store them in a 
[letterpress copybook](http://www2.archivists.org/glossary/terms/l/letterpress-copybook).

 ![Letter](screenshots/letter.png)

### Features ###

 - Highly customized Django Admin
 - Full-text searching with Elasticsearch
 ![Fuzzy text search](screenshots/text_search.png)
 - SQLite database
 - Place mapping with OpenStreetMap and OpenLayers 6
 ![Map](screenshots/map_with_popup.png)
 - Export to text files
 - Word frequency statistics by month, with Bokeh charts
 ![Charts](screenshots/charts.png)
 - Word clouds for writers, date ranges, etc.
 ![Word cloud](screenshots/wordcloud_page.png)
 
### Notes ###
 - Make sure you have write access to the SQLite database file `db.sqlite3`
 - Set up a Django Admin user with the command ```shell python manage.py createsuperuser ```.
 - Elasticsearch index can be created or updated manually with the Django management command `push_to_index`, otherwise updates are automatic when the model is saved.
 - Text searches are fuzzy by default. For exact match, enclose search terms in quotes.

### Setup with Docker ### 
 - Build the `django` and `elasticsearch` services:  
   ```docker-compose -f docker-compose.yml build```
 - Run the `django` and `elasticsearch` services:  
   ```docker-compose -f docker-compose.yml up```
 
### Credits ###
Photograph of copy press from [Letterpress Commons](https://letterpresscommons.com), 
map marker from [Maps Icons Collection](https://mapicons.mapsmarker.com), other images public domain.
Thanks to [Hipster Ipsum](https://hipsum.co/) and [Bacon Ipsum](https://baconipsum.com/) for some of the gibberish text in my unit tests.