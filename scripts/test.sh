#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


. $VIRTUALENV_ROOT/bin/activate

set -a
. test/_fixtures/environment-vars.sh
set +a

coverage run --source=beachfront -m unittest
coverage xml -o report/coverage/coverage.xml
coverage html -d report/coverage/html
coverage report
