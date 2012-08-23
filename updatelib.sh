#!/bin/sh
echo "Getting latest imdbpy"
hg clone https://shrike@bitbucket.org/alberanid/imdbpy lib/imdbpy
ln -s lib/imdbpy/imdb imdb
cd lib/imdbpy
hg pull && hg update
