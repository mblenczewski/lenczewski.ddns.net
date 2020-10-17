#!/bin/bash

ROOT="$(pwd)"

SCRIPTS="${ROOT}/scripts"

SCRATCH="${ROOT}/tmp"
SCRATCHDIRS=("html" "posts")

WEBROOT="${ROOT}/out"
WEBROOTDIRS=("css" "js" "lib" "layouts" "posts")

## setup build environment
[ -d "${SCRATCH}" ] && rm -rf "${SCRATCH}"
[ -d "${WEBROOT}" ] && rm -rf "${WEBROOT}"

mkdir "${SCRATCH}"
mkdir "${WEBROOT}"

for DIR in "${SCRATCHDIRS[@]}"; do
	mkdir "${SCRATCH}/${DIR}"
done

for DIR in "${WEBROOTDIRS[@]}"; do
	mkdir "${WEBROOT}/${DIR}"
done

## $1 :	Source folder
## $2 :	Destination folder
## $3 : File glob
## $4 :	Processing function to invoke for each file found
##	$1 : Source file
##	$2 : Destination file
FOR_FILES () {
	local SRC="${1}"
	local DST="${2}"
	local GLOB="${3}"
	local FUNC="${4}"

	pushd "${SRC}" >/dev/null
	find -name "${GLOB}" -type f -print0 | while read -d $'\0' FILE; do
		"${FUNC}" "${FILE}" "${DST}/${FILE}"
	done
	popd >/dev/null
}

## $1 : Source file
## $2 : Destination file
COLLAPSE_MILD () {
	local SRC="${1}"
	local DST="${2}"
	local TMP=$(mktemp)
	
	cat "${SRC}" | tr -d '\r\t' > "${TMP}"
	cat "${TMP}" > "${DST}"

	rm "${TMP}"
}

## $1 : Source file
## $2 : Destination file
COLLAPSE_STRICT () {
	local SRC="${1}"
	local DST="${2}"
	local TMP=$(mktemp)

	cat "${SRC}" | tr -d '\n\r\t' > "${TMP}"
	cat "${TMP}" > "${DST}"

	rm "${TMP}"
}

## template files, convert markdown to html, and build post index file
. "${ROOT}/env/bin/activate"

OPTS=(\
	"${ROOT}/html/" \
	"${ROOT}/html/layouts/_Layout.html" \
	"${ROOT}/posts/" \
	"${ROOT}/html/layouts/_PostLayout.html" \
	"${SCRATCH}/" \
	"${WEBROOT}/" \
)
python "${SCRIPTS}/build.py" "${OPTS[@]}"

deactivate

## copy over static files into webroot
FOR_FILES "${ROOT}/css" "${WEBROOT}/css" "*.css" cp
FOR_FILES "${ROOT}/js" "${WEBROOT}/js" "*.js" cp
FOR_FILES "${ROOT}/lib" "${WEBROOT}/lib" "*" cp
FOR_FILES "${ROOT}/public" "${WEBROOT}" "*" cp

## clean whitespace from files
FOR_FILES "${WEBROOT}" "${WEBROOT}" "*.html" COLLAPSE_MILD
FOR_FILES "${WEBROOT}" "${WEBROOT}" "*.css" COLLAPSE_STRICT
FOR_FILES "${WEBROOT}" "${WEBROOT}" "*.js" COLLAPSE_STRICT

## clean unnecessary files
rm -rf "${WEBROOT}/layouts"

