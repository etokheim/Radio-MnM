# This script just updates the po files corresponding to the updates made in the project.
# The script is call agnostic, by which we mean it doesn't matter which directory you call
# it from.
#
# The script is not very foolproof yet. Things TODO:
# - Dynamically update all translation .po files, don't hard code it

scriptLocation="$(dirname $(readlink -f "$0"))"
localesLocation="$scriptLocation/../locales"

xgettext \
	--from-code=utf-8 \
	--package-name="Radio M&M" \
	--copyright-holder="Erling Tokheim" \
	--msgid-bugs-address="ertokheim@gmail.com" \
	--language="Python" \
	--package-version=1.0 \
	--default-domain base \
	--output "$localesLocation/base.pot" \
	--language=Python \
	*/*.py

msgmerge --update "$localesLocation/nno/LC_MESSAGES/base.po" "$localesLocation/base.pot"