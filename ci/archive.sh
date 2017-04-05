#!/bin/bash -ex

pushd `dirname $0`/.. > /dev/null
root=$(pwd -P)
popd > /dev/null

source $root/ci/vars.sh

if [ $JENKINS_HOME ]; then
    . /opt/rh/rh-python35/enable
fi

./scripts/package.sh
