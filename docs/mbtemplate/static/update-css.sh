#!/bin/sh

cp ../../../../viur-site/appengine/static/css/viur.css viur-base.css
if [ $? -ne 0 ]
then
	echo "Unable to retrieve viur.css"
	exit 1
fi

sed -e "s/\.\.\/\.\.\/static\/images\///g" viur-base.css > viur.css
rm viur-base.css

echo "Done :-)"

