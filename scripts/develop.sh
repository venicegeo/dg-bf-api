#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


SERVER_PORT=5000
UI_PORT=$(($SERVER_PORT - 1))


################################################################################

(
    . venv/bin/activate

    set -a
    . _environment-vars.sh

    STATIC_BASEURL=http://localhost:$UI_PORT/ \
    gunicorn beachfront.server:server -b localhost:$SERVER_PORT --threads 5 --reload
) &

(
    cd ui
    PORT=$UI_PORT \
    NODE_ENV=development \
    ./node_modules/.bin/webpack-dev-server --hot --host localhost --port $UI_PORT
) &

wait
