#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


. venv/bin/activate

set -a
. _environment-vars.sh

coverage run --source=beachfront -m unittest
coverage report
