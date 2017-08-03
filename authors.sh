#!/bin/bash

set -e


list-repos() {
    cat $inifile | grep -e '^local_folder = ' | sed 's@[^=]*=@@g'
}

#(for i in $(list-repos) ; do
#     cat $i/.mailmap
# done) \
#    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' \
#    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' \
#    | sed  -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' | sort | uniq > ,,all-mailmap
#echo "Generated ,,all-mailmap"

fix-multi-email-in-one-line() {
    local i
    for i in may need multiple replace ; do
        sed -e 's@\([^<]*\) <\([^>]*\)> @\1 <\2>\n\1 @g' -i $1
    done
}
#fix-multi-email-in-one-line ,,all-mailmap

process-repo-old() {
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

check-networks() {
    for r in $(list-repos); do
        echo https://github.com/swcarpentry/${r#,,}/network
    done | xargs firefox
}

check-all-mailmap() {
    echo "#### Looking for duplicates..."
    cat all-mailmap | sed 's@.*<@<@g'| sort | uniq -c | grep -v '^ *1'   ||true
    echo "#### Looking for single-word name..."
    cat all-mailmap | grep '^[^ ]* <'    ||true
    echo "#### Looking in all-mailmap for all names from all-moreinfo..."
    cat all-moreinfo | grep -v '^#' | sed 's@,.*@@g' | while read n; do
        if cat all-mailmap | grep -q "^$n " ; then
            true
        else
            echo "Missing $n in all-mailmap (present in all-moreinfo)"
        fi
    done
}

__obfuscate() {
    \cp "$1" ,,obf
    cat ,,obf | tr '[a-m][n-z][A-M][N-Z]' '[n-z][a-m][N-Z][A-M]' > "$1"
}
obfuscate() {
    # used for commiting cheaply obfuscated emails
    __obfuscate all-mailmap
    __obfuscate all-moreinfo
}

_STYLES=$(pwd)/,,styles-prevent
_STYLES_OK="$_STYLES.ok"
rm -f "$_STYLES_OK"
__check-we-have-localstyles-uptodate-for-authors-filtering() {
    echo ____
    if [ -f "$_STYLES_OK" ] ; then
        return
    fi
    if [ -d "$_STYLES" ] ; then
        git -C "$_STYLES" pull
    else
        git clone https://github.com/swcarpentry/styles.git "$_STYLES"
    fi
    touch "$_STYLES_OK"
}
_check-we-have-localstyles-uptodate-for-authors-filtering() {
    __check-we-have-localstyles-uptodate-for-authors-filtering "$@" 1>&2
}
_git-all-authors() {
    _check-we-have-localstyles-uptodate-for-authors-filtering
    # get a list of effective contributors (remove style contributions)
    if [ "$NOFILTER" != "" ] ; then
        git log --format="%aN" |sort |uniq
    else
        awk 'NR==FNR{a[$1];next} !($1 in a) {$1=""; print $0}' \
            <(git -C "$_STYLES" log --format="%H") \
            <(git log --format="%H %aN") \
            |cut -c 2- |sort |uniq
    fi
}

rm -f ",,.todo-mailmap"
process-repo() {
    local i
    for i in $(list-repos); do
        echo "////////// $i //////////"
        cd $i
        # the ones that actually need something in the mail map (they don't match what we have in the shared one)
        awk 'NR==FNR{a[$0];next}!($0 in a)' ../all-mailmap <(git log --format="%an <%ae>"|sort |uniq) > ../,,diffs

        rm -f ../,,.mailmap
        cat ../,,diffs | while read line ; do
            local n="<${line#*<}"
            repl=$(cat ../all-mailmap | grep -e "$n"'$' | tail -1)
            if test "$repl" '!=' "" ; then
                #echo "Recycling: $repl"
                echo "$repl" >> ../,,.mailmap
            else
                echo "From commit (TODO manual integration, saved to ,,.todo-mailmap): $line"
                echo "$line # TODO" >> ../,,.mailmap
                echo "$line # TODO" >> ../,,.todo-mailmap
            fi
        done
        cat ../,,.mailmap      | sort | uniq > .mailmap
        cat ../,,.todo-mailmap | sort | uniq > ../,,.todo-mailmapclean

        # Now we have the proper mailmap, go on with AUTHORS
        # show it first
        diff <(cat AUTHORS |sort|uniq) <(_git-all-authors) |colordiff
        # add what is missing (remove nothing)
        awk 'NR==FNR{a[$0];next}!($0 in a)' AUTHORS <(_git-all-authors) > ../,,diffs
        cat ../,,diffs | sort | uniq >> AUTHORS
        # remove what should be
        awk 'NR==FNR{a[$0];next}!($0 in a)' <(_git-all-authors) <(cat AUTHORS |sort|uniq) > ../,,diffs
        cat ../,,diffs | while read line ; do
            echo RM:$line
            cp AUTHORS ../,,auth
            cat ../,,auth | grep -v '^'"$line"'$' > AUTHORS
        done
        # WARN + remove single-word names
        cat AUTHORS | grep '^[^ ]*$' | sed 's@^@###### WARN: @g'
        cp AUTHORS ../,,auth
        cat ../,,auth | grep -v '^[^ ]*$' > AUTHORS
        # back
        cd -
    done
}

check-author-diff-summary() {
    local i
    for i in $(list-repos); do
        cd $i
        echo "////////// $i //////////"
        diff <(cat AUTHORS |sort |uniq) <(git log --use-mailmap --format="%aN" |sort |uniq)    ||true
        cd -
    done
}

sort-AUTHORS() {
  echo "Actually, use the python version"
}






#list-repos
#process-repo ,,workshop-template
#check-author-diff-summary | colordiff
#check-all-mail-map

inifile=$1
shift

if test "$inifile" == "--help" ; then
    cat $0 | grep '^[^ ]*() *{ *$' | sed 's@(.*@@g'
    exit
fi

if test "$inifile" == "obfuscate" ; then
    obfuscate
    exit
fi

test -f $inifile
echo "Found ini file $inifile"

if grep __OBFUSCATED__ all-mailmap ; then
    echo "NB: Automatically un-obfuscated all-mailmap"
    echo "    ... should obfuscate before commit, with: $0 obfuscate"
    obfuscate
fi

"$@"

if [ "$RE" != "" ] ; then
    obfuscate
fi

#for i in $(list-repos) ; do
#    process-repo $i
#done

#for i in $(list-repos) ; do
#    process-repo $i
#done
