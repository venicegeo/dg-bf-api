#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


. venv/bin/activate

set -a
. test/_fixtures/environment-vars.sh

coverage run --source=beachfront -m unittest
coverage report
