#!/usr/bin/env bash
# Based on https://github.com/avivace/iosevka-docker/blob/master/run.sh

set -euo pipefail

# Create temporary build directory
mkdir -p /tmp/build
cd /tmp/build

BUILD_FILE="private-build-plans.toml"
BUILD_PARAM="ttf::iosevka-custom"
CUSTOM_BUILD_FILE=true
FONT_VERSION="30.3.2"

# Check the input
if [[ ! -f "/build/$BUILD_FILE" ]]; then
    echo "Custom build-plans file not found"
    exit 1
fi

echo "Using build plan: $BUILD_PARAM"

# Extract downloaded source code
cd $HOME
tar -xf "iosevka.tar.gz"
cd ./*Iosevka-*

if [ "$CUSTOM_BUILD_FILE" = true ]; then
    cp "/build/$BUILD_FILE" .
fi

echo "Building version ${FONT_VERSION}"
npm install
npm run build -- "$BUILD_PARAM"

# Copy the dist folder back to the mounted volume
cp -r dist /build/
