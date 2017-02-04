#!/bin/bash

set -e

inifile=$1
shift

test -f $inifile
echo "Found ini file $inifile"

list-repos() {
    cat $inifile | grep -e '^local_folder = ' | sed 's@[^=]*=@@g'
}

(for i in $(list-repos) ; do
     cat $i/.mailmap
 done) \
    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' \
    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' \
    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' | sort | uniq > ,,all-mailmap
echo "Generated ,,all-mailmap"



fix-multi-email-in-one-line() {
    local i
    for i in may need multiple replace ; do
        sed -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' -i $1
    done
}

fix-multi-email-in-one-line ,,all-mailmap

process-repo() {
    local i=$1
    cd $i
    echo "////////// $i //////////"
    # compute missing names (using mailmap as it may already resolve some namings)
    diff <(git log --use-mailmap --format="%aN" |sort |uniq) <(sort AUTHORS) | grep -e '^< ' | sed 's@^< @@g' > ../,,diffs
    git checkout .mailmap
    fix-multi-email-in-one-line .mailmap
    # fix missing names with the global version, or fill a default from the commit
    cat ../,,diffs | while read n ; do
        e=$(git log --use-mailmap --format="%aN --- %aE" | sort | uniq | grep -e '^'"$n"' ---' | sed 's@.* --- @@g')
        repl=$(cat ../,,all-mailmap | grep "$e" | tail -1)
        if test "$repl" '!=' "" ; then
            echo "Recycling: $repl"
            echo "$repl" >> .mailmap
        else
            #e=$(git log --use-mailmap --format="%aN --- %aE" | sort | uniq | grep -e '^'"$n"' ---' | sed 's@.* --- @@g')
            echo "From commit: $n <$e>"
            echo "$n <$e>" >> .mailmap
        fi
    done
    # enrich the AUTHORS file
    diff <(cat AUTHORS |sort |uniq) <(git log --use-mailmap --format="%aN" |sort |uniq) | grep -e '^> ' | sed 's@^> @@g' > ../,,adds
    cat ../,,adds >> AUTHORS
    # check contents
    diff <(cat AUTHORS |sort |uniq) <(git log --use-mailmap --format="%aN" |sort |uniq)    ||true
    #git diff .mailmap   ||true
    #
    git checkout -B update-mailmap-and-authors
    # back
    cd -
}


check-pull-requests() {
    for r in $(list-repos); do
        echo https://github.com/swcarpentry/${r#,,}/pulls
    done | xargs firefox
}

check-author-diff-summary() {
    local i
    for i in $(list-repos); do
        cd $i
        echo "////////// $i //////////"
        diff <(cat AUTHORS |sort |uniq) <(git log --use-mailmap --format="%aN" |sort |uniq)    ||true
        # back
        cd -
    done
}

list-repos
#process-repo ,,workshop-template
check-author-diff-summary | colordiff

#for i in $(list-repos) ; do
#    process-repo $i
#done

#for i in $(list-repos) ; do
#    process-repo $i
#done

