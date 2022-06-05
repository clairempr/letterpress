FROM python:3.10.1

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libatlas-base-dev gfortran apt-utils && \
    apt-get install -y libsqlite3-mod-spatialite gdal-bin && \
    ln -s /usr/lib/x86_64-linux-gnu/mod_spatialite* /usr/local/lib/

RUN mkdir /code
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt

# Some of the sentiment analysis uses textblob, which requires that data be downloaded
RUN python -m textblob.download_corpora

ADD . /code/
