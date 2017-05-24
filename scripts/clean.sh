#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
################################################################################


echo
echo "Cleaning up"
rm -rfv \
    beachfront.zip \
    beachfront/static/ui \
    ui/npm-debug.log \
    vendor \
    report \
    .coverage \
    manifest.dev.yml \
    manifest.int.yml \
    manifest.stage.yml \
    manifest.prod.yml \
    | sed 's/^/    - /'
