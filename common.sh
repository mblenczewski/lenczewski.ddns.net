#!/bin/sh

LAYOUTS=html/layouts
SCRIPTS=scripts
TMP=tmp
OUT=out

[ -d ${TMP} ] || mkdir ${TMP}
[ -d ${OUT} ] || mkdir ${OUT}

## $1 :	Source folder
## $2 :	Destination folder
## $3 : File glob
## $4 :	Processing function to invoke for each file found
##	$1 : Source file
##	$2 : Destination file
FOR_FILES () {
	OLDDIR="$(pwd)"
	cd "${1}"

	find -name "${3}" -type f -print | while read F; do
		mkdir -p $(dirname "${2}/${F}") && "${4}" "${F}" "${2}/${F}"
	done

	cd "${OLDDIR}"
}

