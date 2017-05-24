#!/bin/bash -ae

cd $(dirname $(dirname $0))  # Return to root

. scripts/_check_environment.sh
################################################################################


python scripts/user-admin.py add "$@"
