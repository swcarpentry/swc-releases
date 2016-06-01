
# Meant to be source'd

# same as in "make-or-update-release.sh" but for write access
resolve-lesson() {
    if [[ ${1:0:3} == 'dc:' ]] ; then
        printf %s "git@github.com:datacarpentry/${1:3}.git"
    else
        printf %s "git@github.com:swcarpentry/$1.git"
    fi
}

# this one may need to be updated once we use the new build system
clonelatest-branch-build-commit() {
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
        git commit -m "Rebuilt HTML files for release $vers"
        git diff HEAD~
        git log
        echo Will git push unless you Ctrl+C
        read DUMMY
        git push --set-upstream origin $vers
        cd -
    } || cd -
}

patchcss-commit() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    as=$1
    vers=$2
    repo=$(resolve-lesson $as)
    css=css/swc.css
    cd ,,$as && {
        if grep -q 'version added automatically' $css ; then
            echo "INFO: seems already patched, removing the end of it"
            \cp $css ,,css
            cat ,,css | awk '/version added automatically/ {exit} {print}' > "$css"
        fi
        cat <<EOF >> $css
/* version added automatically */
div.banner::before {
    content: "Version $vers";
    font-size: 10px;
    font-family: monospace;
    font-weight: bold;
    line-height: 1;
    /* */
    position: fixed;
    right: 0;
    bottom: 0;
    z-index: 10;
    /* */
    color: white;
    background: rgb(43, 57, 144);
    padding: 3px;
    border: 1px solid white;
}
EOF
        git add $css
        git commit -m "Added version ($vers) to pages via CSS"
        git diff HEAD~
        git log
        echo Will git push unless you Ctrl+C
        read DUMMY
        git push --set-upstream origin $vers
        cd -
    } || cd -
}

custom1() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        clonelatest-branch-build-commit $i 2016.06-alpha
    done
}

custom2() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        echo '### ' $i
        patchcss-commit $i 2016.06-alpha
    done
}

custom3() {
    git submodule update --remote -- 2016.06-alpha/*
}
