#!/bin/bash -ex

export MANIFEST_FILENAME=manifest.int.yml

export GEOAXIS_HOST=gxisaccess.gxaccess.com
export CATALOG_HOST=bf-ia-broker.int.geointservices.io
export PIAZZA_HOST=piazza.int.geointservices.io

./ci/_cf_push.sh
