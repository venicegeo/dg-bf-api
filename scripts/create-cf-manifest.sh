#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################

err=''
[ -z "$CATALOG_HOST" ] && { err+='\n  - CATALOG_HOST cannot be blank'; }
[ -z "$PIAZZA_HOST" ] && { err+='\n  - PIAZZA_HOST cannot be blank'; }
[ -z "$PIAZZA_AUTH" ] && { err+='\n  - PIAZZA_AUTH cannot be blank'; }
[ -z "$MANIFEST_OUTFILE" ] && { err+='\n  - MANIFEST_OUTFILE cannot be blank'; }
[ -z "$err" ] || { echo -e "Error: Invalid environment:\n$err"; exit 1; }

echo ###########################################################################

piazza_url=https://$PIAZZA_HOST/v2/key



# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
# FIXME -- remove this when the SSL cert SubjectAltName problem is fixed
function curl() {
    echo "
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        WARNING

        curl is about to be invoked without SSL verification on URL:

            '$(echo $@ | grep -Eo "https?://[^ ]+")'

        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    " | sed 's/^        //g' >&2

    echo -en "\nPausing for effect" >&2
    for n in {1..5}; do
        echo -n . >&2
        sleep 1
    done
    echo -en '\r                           \r' >&2

    /usr/bin/curl --insecure "$@"
}
# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK



curl "https://${PIAZZA_HOST}" -fs >/dev/null || { echo "Error: Piazza is unreachable"; exit 1; }

echo "Requesting new Piazza API key via '$piazza_url'"

response=$(curl -s $piazza_url -u "$PIAZZA_AUTH")
echo "$response" | sed 's/^/    | /'

piazza_api_key=$(echo $response|grep -oE '\w{8}-\w{4}-\w{4}-\w{4}-\w{12}'||true)

[ -z "$piazza_api_key" ] && { echo -e "\nError: No Piazza API key found"; exit 1; }

echo ###########################################################################

echo "Writing to '$MANIFEST_OUTFILE':"
cat manifest.yml |\
    sed "s/CATALOG_HOST: ~/CATALOG_HOST: $CATALOG_HOST/" |\
    sed "s/PIAZZA_HOST: ~/PIAZZA_HOST: $PIAZZA_HOST/" |\
    sed "s/PIAZZA_API_KEY: ~/PIAZZA_API_KEY: $piazza_api_key/" |\
    tee $MANIFEST_OUTFILE |\
    sed 's/^/    | /'
