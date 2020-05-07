scriptLocation="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"
localesLocation="$scriptLocation/../locales"

msgfmt -o "$localesLocation/nno/LC_MESSAGES/base.mo" "$localesLocation/nno/LC_MESSAGES/base"