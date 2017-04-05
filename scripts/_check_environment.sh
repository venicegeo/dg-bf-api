#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
################################################################################


VIRTUALENV_ROOT=venv
ENVIRONMENT_FILE=_environment-vars.sh
UI_ROOT=ui


################################################################################

if [ ! -d "$VIRTUALENV_ROOT" -o ! -f "$ENVIRONMENT_FILE" -o ! -d "$UI_ROOT/node_modules" ]; then
    echo -e "It looks like your development environment is not properly set up.\n"
    read -p "Would you like to set it up now (y/N)? " -r

    if [[ ! "$REPLY" =~ ^[Yy] ]]; then
        echo -e "\nExiting...\n"
        exit 1
    fi

    echo
    printf '=%.0s' {1..80}
    echo

    ############################################################################

    echo -e "\nCreating virtual Python environment at '$VIRTUALENV_ROOT'\n"

    rm -rf $VIRTUALENV_ROOT

    python3 -m venv venv

    . venv/bin/activate

    echo -e "\nInstalling Python dependencies\n"

    pip install -r requirements.txt


    ############################################################################

    echo -e "\nCreating environment vars file at '$ENVIRONMENT_FILE'\n"

    rm -rf $ENVIRONMENT_FILE

    echo "
    export PIAZZA_API_KEY=
    export PORT=5000
    " > $ENVIRONMENT_FILE


    ############################################################################

    echo -e "\nInstalling Node dependencies at '$UI_ROOT'\n"

    rm -rf $UI_ROOT/node_modules

    (
        cd ui
        npm install
    )

    echo
    printf '=%.0s' {1..80}
    echo
fi
