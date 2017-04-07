#!/bin/bash -ex

export MANIFEST_FILENAME=manifest.stage.yml

export GEOAXIS_HOST=gxisaccess.gxaccess.com
export CATALOG_HOST=bf-ia-broker.stage.geointservices.io
export PIAZZA_HOST=piazza.stage.geointservices.io

./ci/_cf_push.sh
