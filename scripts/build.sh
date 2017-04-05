#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


echo -e "\nBuilding UI\n"

cd ui

set -a
. _environment-vars.sh

NODE_ENV=production \
./node_modules/.bin/webpack --hide-modules
