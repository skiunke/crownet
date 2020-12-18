#!/bin/bash
# Update a container within the rover container registry.
#
IMAGE_SHORT="$1"
RANDOM=$(date +%s)
REGISTRY='sam-dev.cs.hm.edu:5023'
IMAGE_LONG="$REGISTRY/rover/rover-main/$IMAGE_SHORT"
VERSION_TAG="$2"
DATE_TAG="$(date "+%y%m%d-%H%M")"

if [ -z "$IMAGE_SHORT" ]; then
    echo "Illegal number of command line arguments."
    echo "Usage: $0 [container_short_name] [version_tag] [additional arguments to be passed to docker]"
    exit -1
fi

if [ -z "$VERSION_TAG" ]; then
    echo "No version tag specified - using default tag \"latest\"."
    VERSION_TAG="latest"
fi


echo "Building $IMAGE_SHORT ..."
docker build -t "$IMAGE_LONG:$VERSION_TAG" -t "$IMAGE_LONG:$DATE_TAG" --build-arg NOCACHE_PULL=$RANDOM ${@:3:${#@}+1-3} .

if [ $? -eq 0 ]; then
   docker login "$REGISTRY"
#   docker push "$IMAGE_LONG:$VERSION_TAG"
#   docker push "$IMAGE_LONG:$DATE_TAG"
else
   echo "Container build did not succeed - $IMAGE_SHORT not uploaded to registry."
fi
