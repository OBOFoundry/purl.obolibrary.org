#!/bin/sh
NAME="purl.obolibrary.org:latest"
DIR="/var/www/purl.obolibrary.org"
docker build -t "${NAME}" . || exit 1
docker run -v "${PWD}":"${DIR}" -w "${DIR}" --rm -it "${NAME}" "$@" || exit 1
