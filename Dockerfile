FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libatlas-base-dev gfortran apt-utils && \
    apt-get install -y libspatialite-dev gdal-bin && \
    ln -s /usr/lib/x86_64-linux-gnu/libspatialite* /usr/local/lib/

RUN mkdir /code
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt
ADD . /code/

