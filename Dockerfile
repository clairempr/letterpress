FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libatlas-base-dev gfortran apt-utils && \
    apt-get install -y libsqlite3-mod-spatialite gdal-bin && \
    ln -s /usr/lib/x86_64-linux-gnu/mod_spatialite* /usr/local/lib/

RUN mkdir /code
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt

# Modify libgeos.py to avoid the error
# django.contrib.gis.geos.error.GEOSException: Could not parse version info string "3.7.1-CAPI-1.11.1 27a5e771"
RUN sed -i 's/ver = geos_version().decode()/ver = geos_version().decode().split(" ")[0]/' /usr/local/lib/python3.5/site-packages/django/contrib/gis/geos/libgeos.py

# Some of the sentiment analysis uses textblob, which requires that data be downloaded
RUN python -m textblob.download_corpora

ADD . /code/
