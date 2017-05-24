#!/bin/bash -ae

cd $(dirname $(dirname $0))  # Return to root

. scripts/_check_environment.sh
################################################################################


. $VIRTUALENV_ROOT/bin/activate

set -a
. $ENVIRONMENT_FILE
set +a

export MUTE_LOGS=1

python -m beachfront.temporary_cli_for_user_admin "$@"
