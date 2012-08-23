#!/bin/sh
echo "Getting latest imdbpy"
hg clone https://shrike@bitbucket.org/alberanid/imdbpy lib/imdbpy
ln -s lib/imdbpy/imdb imdb
cd lib/imdbpy
hg pull && hg update

echo "Updating requests"
git clone git://github.com/kennethreitz/requests.git lib/requests
ln -s lib/requests/requests requests
cd lib/requests
git pull

