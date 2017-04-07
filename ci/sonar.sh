#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

## Install Dependencies ########################################################

# HACK -- workaround for Python 3.5 in Jenkins
if [ $JENKINS_HOME ]; then
    . /opt/rh/rh-python35/enable
fi

echo yes | ./scripts/test.sh
