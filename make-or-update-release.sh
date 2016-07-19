#!/bin/bash

### Script setup
set -e
W=$(dirname $(readlink -f $0))


### Tools
resolve-lesson() {
    if [[ ${1:0:3} == 'dc:' ]] ; then
        printf %s "https://github.com/datacarpentry/${1:3}.git"
    else
        printf %s "https://github.com/swcarpentry/$1"
    fi
}
is-tag() {
    test "$2" = v5.3
    return 
    # might need auth... to avoid rate limits
    curl -s "${1/github.com/api.github.com\/repos}/git/refs/tags/$2" | grep -q '"ref"'
}
is-branch() {
    test "$2" != v5.3
    return
    curl -s "${1/github.com/api.github.com\/repos}/git/refs/heads/$2" | grep -q '"ref"'
}
fail() {
    echo "... fail"
    exit
}
progress() {
    echo "    #### $@"
}
ensure-git-version-is-at-least() {
    local v
    v=$(git version | awk '{print $NF}' | tr -d '.')
    if test "$v" -lt "$1" ; then
        echo "Expected git version at least $1, found $v"
        false
    fi
}

#if [ "$(pwd)" = "$W" ] ; then
#    echo "This script should probably not be run run from the $W folder, but rather from its parent."
#    exit
#fi

if [ $# -lt 2 ] ; then
    echo "Requires a release name and a list of lessons (can be empty for updates)" 
    exit
fi

TARGET=$1
shift
TAG=${TAG-$TARGET}

progress "- Working on release '${TAG}' in folder '${TARGET}'."

if [ "${ONLYHTML}" != "" ] ; then
    progress "- ONLYHTML is set, skipping generation/update"
    cd "${TARGET}"
elif [ -d ${TARGET} ] ; then
    progress "- Folder '${TARGET} is present, making an update"
    progress "- TODO"
    cd "${TARGET}"
else
    progress "- Folder '${TARGET}' is absent, making it and starting a new release"
    mkdir "${TARGET}"
    cd "${TARGET}"
    progress "- Trying to add submodules for each lesson"
    for L in "$@"; do
        progress "  - Adding submodule for lesson '$L'"
        l=$(resolve-lesson "$L")
        if is-branch "$l" "$TAG" ; then
            ensure-git-version-is-at-least 182 # for submodule with branch
            progress "    - it is a branch, adding a tracking submodule"
            git submodule add --force -b "$TAG" "$l"
        elif is-tag "$l" "$TAG" ; then
            progress "    - it is a tag, adding a simple submodule"
            # the "--force" avoids recloning every time we try the script
            git submodule add --force "$l"
            (cd "$L" && git checkout "$TAG")
        else
            progress "$TAG is neither a branch nor a tag"
            fail
        fi
    done
fi

progress "- Now (re)generating the index"

progress "  - making the dummy HTML index"
cat <<EOF > index.html
<!doctype html>
<html class="no-js" lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body>
  <ul>
EOF
for L in "$@"; do
    echo "<li><a href='$L/index.html'>$L (${TAG})</a></li>" >> index.html
done
echo "  </ul>" >> index.html
echo "</body>" >> index.html
progress "  - adding index.html to git"
git add index.html

progress "- FINISHED WITH NO ERRORS"
progress "  you may review it and commit/push, e.g., with"
progress ""
progress "    git status"
progress "    git commit -m 'Release ${TAG}'"
progress "    git push"
progress ""
