@echo off

python scripts/build_html.py

:: Export from 'public' directory
robocopy public out /S /is /it /NJH /NJS

:: Minify HTML
set html-minifier-vars=--collapse-whitespace --remove-comments --remove-optional-tags --remove-redundant-attributes --remove-script-type-attributes --remove-tag-whitespace --minify-css true --minify-js true
forfiles /p out /s /m *.html /c "cmd /c html-minifier %html-minifier-vars% @file -o @file"

:: Export CSS
mkdir out\\styles
forfiles /p styles /s /m *.css /c "cmd /c csso @file -o ..\\out\\styles\\@file"
