
# Meant to be source'd

# same as in "make-or-update-release.sh" but for write access
resolve-lesson() {
    if [[ ${1:0:3} == 'dc:' ]] ; then
        printf %s "git@github.com:datacarpentry/${1:3}.git"
    else
        printf %s "git@github.com:swcarpentry/$1.git"
    fi
}

# slightly more modular than below
do-clone() {
    if test $# -lt 1 ; then
        echo "Expect <repo>"
        return
    fi
    as=$1
    repo=$(resolve-lesson $as)
    git clone $repo ,,$as --depth=1 --no-single-branch
}
do-checkout() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <ref> [new-branch]"
        return
    fi
    as=$1
    ref=$2
    branchit=$3
    repo=$(resolve-lesson $as)
    MINUSB=-b
    if [[ "$FORCE" != "" ]] ; then
        MINUSB=-B
    fi
    (cd ,,$as && {
            git checkout $ref
            if [[ "$branchit" != "" ]] ; then
                git checkout $MINUSB $branchit
            fi
    })
}
do-add-css() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    as=$1
    vers=$2
    repo=$(resolve-lesson $as)
    css=css/swc.css
    (cd ,,$as && {
            if grep -q 'version added automatically' $css ; then
                echo "INFO: seems already patched, removing the end of it"
                \cp $css ,,css
                cat ,,css | awk '/version added automatically/ {exit} {print}' > "$css"
            fi
            gen-css $vers >> $css
            git add $css
            git commit $MORECOMMIT -m "Added version ($vers) to all pages via CSS"
    })
}
do-rebuild-pandoc() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    as=$1
    vers=$2
    repo=$(resolve-lesson $as)
    (cd ,,$as && {
            make clean preview
            git add *.html
            git commit -m "Rebuilt HTML files for release $vers"
    })
}
do-diff-log() {
    if test $# -lt 1 ; then
        echo "Expect <repo>"
        return
    fi
    as=$1
    repo=$(resolve-lesson $as)
    (cd ,,$as && {
            git diff HEAD~
            git log
    })
}
do-push() {
    if test $# -lt 1 ; then
        echo "Expect <repo>"
        return
    fi
    as=$1
    repo=$(resolve-lesson $as)
    (cd ,,$as && {
            echo "Will git push unless you Ctrl+C (press enter to continue)"
            $READ read DUMMY
            $PUSH git push $MOREPUSH
    })
}
do-push-upstream() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    as=$1
    vers=$2
    repo=$(resolve-lesson $as)
    (cd ,,$as && {
            echo "Will git push unless you Ctrl+C (press enter to continue)"
            $READ read DUMMY
            $PUSH git push $MOREPUSH --set-upstream origin $vers
    })
}

do-1() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do

        v=2015.08
        #do-clone $i

        FORCE=1 do-checkout $i v5.3 $v
        do-add-css $i $v
        #do-diff-log $i

        #MOREPUSH=--force
        READ=echo do-push-upstream $i $v
    done
}

do-postBBQ() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do

        v=2016.06-beta
        do-clone $i # if not cloned yet (else, comment it)

        do-checkout $i gh-pages $v # branch the latest version, as $v
        do-rebuild-pandoc # if need to rebuilt (need a recent PANDOC)
        do-add-css $i $v
        #do-diff-log $i  # to see what changed

        do-push-upstream $i $v
        #MOREPUSH=--force     do-push-upstream $i $v    # to force push
    done
    echo "If you pushed to all repositories, you can go on with:"
    echo "make 2016.06-beta"
    echo "git commit"
    echo "git push"
}




do-2() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        v=2016.06-alpha
        do-clone $i
        do-checkout $i $v
        do-rebuild-pandoc $i $v
        do-diff-log $i
        do-push-upstream $i $v
    done
    # make update-submodules
}

gen-css() {
        cat <<EOF
/* version added automatically */
div.banner::before {
    content: "Version $1";
    font-size: 10px;
    font-family: monospace;
    font-weight: bold;
    line-height: 1;
    /* */
    position: fixed;
    right: 0;
    top: 0;
    z-index: 10;
    /* */
    color: white;
    background: rgb(43, 57, 144);
    padding: 3px;
    border: 1px solid white;
}
EOF
}







# this one may need to be updated once we use the new build system
clonelatest-branch-build-commit() {
    if test $# -lt 2 ; then
        echo "Expect <repo> <version>"
        return
    fi
    clone-branch-build-commit "$1" gh-pages "$2"
}

clone-branch-build-commit() {
    if test $# -lt 3 ; then
        echo "Expect <repo> <ref> <version>"
        return
    fi
    as=$1
    ref=$2
    vers=$3
    repo=$(resolve-lesson $as)
    git clone $repo ,,$as --depth=1 --no-single-branch && cd ,,$as && ({
        git checkout $ref
        git checkout -b $vers
        make clean preview
        git add *.html
        git commit -m "Rebuilt HTML files for release $vers" && git diff HEAD~
        git log
        echo Will git push unless you Ctrl+C
        $READ read DUMMY
        $PUSH git push --set-upstream origin $vers
        cd -
    } || cd -)
}







# this one was used to generate the alpha version, using the latest master at the time
custom1() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        clonelatest-branch-build-commit $i 2016.06-alpha
    done
}

# this one to add (or readd with the parameters) the css patch to the alpha version
custom2() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        echo '### ' $i
        MORECOMMIT=--amend MOREPUSH=--force patchcss-commit $i 2016.06-alpha
    done
}

# (1 shot), to create the 2015.08 from v5.3
custom4() {
    for i in shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation ; do
        READ=echo PUSH=echo clone-branch-build-commit $i v5.3 2015.08
    done
}
