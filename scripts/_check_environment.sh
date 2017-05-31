#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
################################################################################


export VIRTUALENV_ROOT=venv
export ENVIRONMENT_FILE=_environment-vars.sh


################################################################################

if [ ! -d "$VIRTUALENV_ROOT" -o ! -f "$ENVIRONMENT_FILE" ]; then
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

    if ! (which python3 && python3 -c 'import sys; assert sys.version_info >= (3, 5, 0)') >/dev/null 2>&1; then
        echo -e "\nPython 3.5.0 or higher must be installed first"
        exit 1
    fi

    virtualenv --python=python3 $VIRTUALENV_ROOT

    . $VIRTUALENV_ROOT/bin/activate

    echo -e "\nInstalling Python dependencies\n"

    pip install -r requirements.txt


    ############################################################################

    echo -e "\nCreating environment vars file at '$ENVIRONMENT_FILE'\n"

    rm -rf $ENVIRONMENT_FILE

    echo 'CONFIG=development' >> $ENVIRONMENT_FILE
    echo 'PIAZZA_API_KEY=' >> $ENVIRONMENT_FILE


    ############################################################################

    echo
    printf '=%.0s' {1..80}
    echo
fi
