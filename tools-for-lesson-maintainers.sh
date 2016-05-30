
# Meant to be source'd

# same as in "make-or-update-release.sh" but for write access
resolve-lesson() {
    printf %s "git@github.com:swcarpentry/$1.git"
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
    git clone $repo ,,$as --depth=1 && cd ,,$as && {
        git checkout -b $vers
        make clean preview
        git add *.html
        git commit -m "Rebuilt HTML files for release $as"
        git log
        echo Will git push unless you Ctrl+C
        read DUMMY
        git push --set-upstream origin $vers
        cd -
    } || cd -
}



