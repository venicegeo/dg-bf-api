#!/bin/bash -e

[ -z $PIAZZA_HOST ] && { echo "Cannot read PIAZZA_HOST from the environment"; exit 1; }
[ -z $CATALOG_HOST ] && { echo "Cannot read CATALOG_HOST from the environment"; exit 1; }
[ -z $GEOAXIS_HOST ] && { echo "Cannot read GEOAXIS_HOST from the environment"; exit 1; }
[ -z $MANIFEST_FILENAME ] && { echo "Cannot read MANIFEST_FILENAME from the environment"; exit 1; }
[ -z $BEACHFRONT_PIAZZA_AUTH ] && { echo "Cannot read BEACHFRONT_PIAZZA_AUTH from the environment"; exit 1; }
[ -z $GEOAXIS_CLIENT_ID ] && { echo "Cannot read GEOAXIS_CLIENT_ID from the environment"; exit 1; }
[ -z $GEOAXIS_CLIENT_SECRET ] && { echo "Cannot read GEOAXIS_CLIENT_SECRET from the environment"; exit 1; }

echo ###########################################################################

piazza_url=https://$PIAZZA_HOST/v2/key

echo "Requesting new Piazza API key via $piazza_url"
response=$(curl -s $piazza_url -u "$BEACHFRONT_PIAZZA_AUTH")
echo
echo "Response:"
echo $response|sed 's/^/    | /'

piazza_api_key=$(echo $response|grep -oE '\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')
if [ -z $piazza_api_key ]; then
    echo "No Piazza API key found"
    exit 1
fi

echo ###########################################################################

manifest_filename=$MANIFEST_FILENAME
echo "Writing Cloud Foundry manifest to $manifest_filename:"
cat manifest.jenkins.yml |\
    sed "s/CATALOG_HOST: ~/CATALOG_HOST: $CATALOG_HOST/" |\
    sed "s/GEOAXIS_HOST: ~/GEOAXIS_HOST: $GEOAXIS_HOST/" |\
    sed "s/GEOAXIS_CLIENT_ID: ~/GEOAXIS_CLIENT_ID: $GEOAXIS_CLIENT_ID/" |\
    sed "s/GEOAXIS_CLIENT_SECRET: ~/GEOAXIS_CLIENT_SECRET: $GEOAXIS_CLIENT_SECRET/" |\
    sed "s/PIAZZA_HOST: ~/PIAZZA_HOST: $PIAZZA_HOST/" |\
    sed "s/PIAZZA_API_KEY: ~/PIAZZA_API_KEY: $piazza_api_key/" |\
    tee $manifest_filename |\
    sed 's/^/    | /'

echo ###########################################################################
