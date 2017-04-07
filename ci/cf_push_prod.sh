#!/bin/bash -ex

export MANIFEST_FILENAME=manifest.prod.yml

export GEOAXIS_HOST=gxisaccess.gxaccess.com
export CATALOG_HOST=bf-ia-broker.geointservices.io
export PIAZZA_HOST=piazza.geointservices.io

./ci/_cf_push.sh
