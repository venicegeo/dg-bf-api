#!/bin/bash -e

cd $(dirname $(dirname $0))  # Return to root
. scripts/_check_environment.sh
################################################################################


ARCHIVE_FILENAME='beachfront.zip'
FILE_LIST="
    beachfront/
    vendor/
    sql/
    Procfile
    requirements.txt
    runtime.txt
"

################################################################################

./scripts/build.sh

################################################################################

echo -e "\nCollecting Python dependencies\n"

(
    . venv/bin/activate
    mkdir -p vendor
    pip install -d vendor -r requirements.txt
)

################################################################################

echo -e "\nBuilding archive\n"

rm -f $ARCHIVE_FILENAME

zip -r $ARCHIVE_FILENAME $FILE_LIST -x "*/__pycache__/*" "*.pyc" "*.pyo" "*." "beachfront/config/development.py"
