scriptLocation="$(dirname $(readlink -f "$0"))"
localesLocation="$scriptLocation/../locales"

msgfmt -o "$localesLocation/nno/LC_MESSAGES/base.mo" "$localesLocation/nno/LC_MESSAGES/base"