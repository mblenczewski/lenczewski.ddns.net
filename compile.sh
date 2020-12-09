#!/bin/bash

ROOT="$(pwd)"

LAYOUTS="${ROOT}/html/layouts"
SCRIPTS="${ROOT}/scripts"
SCRATCH="${ROOT}/tmp"
WEBROOT="${ROOT}/out"

## setup build environment
[ -d "${SCRATCH}" ] && rm -rf "${SCRATCH}"
[ -d "${WEBROOT}" ] && rm -rf "${WEBROOT}"
mkdir "${SCRATCH}" "${WEBROOT}"

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
		mkdir -p $(dirname "${DST}/${FILE}") && \
			"${FUNC}" "${FILE}" "${DST}/${FILE}"
	done
	popd >/dev/null
}

## $1 : Source file
## $2 : Destination file
## $3 : Stipped characters
COLLAPSE () {
	local SRC="${1}"
	local DST="${2}"
	local STRIPPED_CHARS="${3}"
	local TMP=$(mktemp)
	
	cat "${SRC}" | tr -d "${STRIPPED_CHARS}" > "${TMP}"
	cat "${TMP}" > "${DST}"

	rm "${TMP}"
}

## $1 : Source file
## $2 : Destination file
COLLAPSE_MILD () {
	COLLAPSE "${1}" "${2}" '\r\t'
}

## $1 : Source file
## $2 : Destination file
COLLAPSE_STRICT () {
	COLLAPSE "${1}" "${2}" '\n\r\t'
}

## template files, convert markdown to html, and build post index file
. "${ROOT}/env/bin/activate"

SCRIPT_DIRS=(\
	"html" \
	"posts"
)
for DIR in "${SCRIPT_DIRS[@]}"; do
	mkdir "${SCRATCH}/${DIR}" "${WEBROOT}/${DIR}"
done

OPTS=(\
	"${ROOT}/html/" \
	"${LAYOUTS}/_Layout.html" \
	"${ROOT}/posts/" \
	"${LAYOUTS}/_PostLayout.html" \
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

