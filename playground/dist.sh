#!/bin/sh

set -e

PLAYGROUND_PATH=$(dirname "$(realpath "$0")")
. $PLAYGROUND_PATH/env.sh

TARGET_PLATFORMS="linux_musl_x86_64
                  windows_amd64"

cd $ROOT_PATH
rm -rf $DIST_PATH
mkdir -p $DIST_PATH

for TARGET_PLATFORM in $TARGET_PLATFORMS; do
    export TARGET_PLATFORM
    $PYTHON -m doit clean_all
    $PYTHON -m doit
    cp $ROOT_PATH/build/py/*.whl $DIST_PATH
done

IMAGES="linux/amd64/build-hat-controller:debian11-cpy3.12
        linux/arm64/v8/build-hat-controller:debian11-cpy3.12
        linux/arm/v7/build-hat-controller:debian11-cpy3.12"

for IMAGE in $IMAGES; do
    $PYTHON -m doit clean_all
    DOCKERFILE=$PLAYGROUND_PATH/dockerfiles/$(echo $IMAGE | cut -d ':' -f 2)
    PLATFORM=$(dirname $IMAGE)
    IMAGE_ID=$(podman images -q $IMAGE)
    podman build --platform $PLATFORM \
                 -f $DOCKERFILE \
                 -t $IMAGE \
                 .
    if [ -n "$IMAGE_ID" -a "$IMAGE_ID" != "$(podman images -q $IMAGE)" ]; then
        podman rmi $IMAGE_ID
    fi
    podman run --rm \
               --platform $PLATFORM \
               -v $DIST_PATH:/hat/dist \
               -v ~/.cache/pip:/root/.cache/pip \
               -i $IMAGE /bin/sh - << EOF
set -e
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip hat-json
./playground/requirements.sh > requirements.pip.txt
pip install --upgrade -r requirements.pip.txt
doit clean_all
doit
cp build/py/*.whl dist
EOF
done

$PYTHON -m doit clean_all
