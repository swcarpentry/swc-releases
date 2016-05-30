
# Meant to be source'd

resolve-lesson() {
    printf %s "https://github.com/swcarpentry/$1"
}

# this one may need to be updated once we use the new build system
clone-branch-build-commit() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    as=$1
    vers=$2
    repo=$(resolve-lesson $as)
    git clone $repo ,,$as --depth=1 \
        && cd ,,$as \
        && git checkout -b $vers \
        && make clean preview \
        && git add *.html \
        && git commit -m "Rebuilt HTML files for release $as" \
        && cd -
}



