#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


echo -e "\nBuilding UI\n"

cd ui
NODE_ENV=production \
./node_modules/.bin/webpack --hide-modules
