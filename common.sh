#!/bin/sh

if [ ! -d env ]; then
	python -m venv env

	. env/bin/activate
	pip install -r requirements.txt
	deactivate
fi

LAYOUTS=layouts
SCRIPTS=scripts
TMP=tmp
OUT=out

[ -d $TMP ] || mkdir $TMP
[ -d $OUT ] || mkdir $OUT
