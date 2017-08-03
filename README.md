# swc-releases
Container for Software Carpentry lesson releases

- <http://swcarpentry.github.io/swc-releases/2017.02/>
- <http://swcarpentry.github.io/swc-releases/2016.06/>
- <http://swcarpentry.github.io/swc-releases/2015.08/> (5.3)

<!-- - <http://swcarpentry.github.io/swc-releases/2016.06-alpha/> (pre-bbq) -->


# Release Model: as of 2017.02

Pre task: ensure AUTHORS are ok in all repositories

Pre setup:

- `cp private.teplate.ini private.ini`
- edit `private.ini` and set your access keys in it
- install/update some R packages (see below for now)
- use `python3 rel.py 1 --version 2017.02` to generate a template ini file from the latest version
- cp `auto.ini 2017.02.ini` (you might edit this file or the generator code if you need fine tuning)

Fully semi-automated with the following steps (create the branches, build and zenodo):

- use `python3 rel.py A B ...`, where `B` is your .ini file, and `A` will take the values
    - `2` will clone the repositories, you can pass a git depth with `--depth` to make the clone faster/smaller
    - `3` will get the sha1 corresponding to the tip of `gh-pages`, you can then edit the .ini file if you want to release older versions for certain repositories
    - `4` will create the (empty) Zenodo submissions, adding some identifiers in the .ini file
    - `5` will create the branches, build the lessons, and push
    - `6` will gather info from the repositories, filling the the .ini with it
    - `7` will fill-in or update the Zenodo submissions
    - `8` will zip the lessons into the `zips/` folder (by default)
    - `9` will upload the zips to Zenodo, you can later re-upload by removing the `zenodo_file` in the ini file, and pass `--force-replace`
    - ~~`final-publish-zenodo` to publish Zenodo submissions, meaning they **won't be deletable afterwards**~~ it is recommended to do it manually on the Zenodo website, to be sure there are no mistakes before publishing

Then, we need to setup the actual hosting on <http://swcarpentry.github.io/swc-releases/20??.??/>.
For now, it uses the old tool:

- one need to update the `Makefile` and run it

### NB: compared to before

- we are acting the fact that the complete process is done by the releaser (no distinction between the role of lesson maintainers and release creator)
- we use a descriptor file (that also get enriched), from which we generate the everything (Zenodo, branches, ...)
- rewrote and wrote a big part of the process in python (branches, zenodo, etc)



# RANDOM NOTES 2017-08 (while updating and releasing)

Preparing and getting latest versions (anyway there will be some implementation work, this time, to get the author list up to date (with opt-out))

    python3 rel.py 1 --version 2017-08
    mv auto.ini 2017-08.ini
    ##DO: manually remove instructor training as we are not releasing it
    python3 rel.py git-for-all 2017-08.ini branch
    python3 rel.py git-for-all 2017-08.ini checkout gh-pages
    python3 rel.py git-for-all 2017-08.ini branch
    python3 rel.py git-for-all 2017-08.ini pull

Now, let's tune the authors (this time, it involves some implementation, so it will probably change for the next release)

    ./authors.sh --help
    alias A='./authors.sh 2017-08.ini'

    A check-pull-requests
    #^ not so clean, too many to actually check now

    A check-all-mailmap
    ##DO: manually removed one duplicate
    ##DO: manually created and fixed all-moreinfo

    A process-repo
    emacs ,,.todo-mailmapclean all-mailmap
    ##DO: add manually, sort-lines, and look for proper names for each TODO, ... very tedious
    ##^ use 'zz-...' when not really found
    A check-all-mailmap
    ##DO: continue fixing, checking also all "Missing" to find typos (but many have actually not commited anything or on instructor-training which is not in this release?)

Now that we have a decent global mailmap, let's patch all repositories (with their own .mailmap and AUTHORS). This is the occasion to list as AUTHORS only the ones that: contributed (outside `style` and did not opt out for these commits, this is automated).

    python3 rel.py git-for-all 2017-08.ini checkout -- .mailmap AUTHORS
    A process-repo
    python3 rel.py sort-authors 2017-08.ini
    python3 rel.py git-for-all 2017-08.ini diff


# RANDOM NOTES 2017-06-03 (somewhat jibberish)

    python3 rel.py 1 --version 9999-none
    python3 rel.py git-for-all auto.ini branch
    python3 rel.py git-for-all auto.ini checkout gh-pages
    python3 rel.py git-for-all auto.ini branch
    python3 rel.py git-for-all auto.ini pull

    head -6 auto.ini > tmp.ini    

    ./authors.sh tmp.ini check-author-diff-summary
    
    tail -13 auto.ini |head -7 > tmp.ini
    # or a pair of lesson or anything, or start from some reduced 2017.02
    
    python3 rel.py git-for-all tmp.ini stash
    python3 rel.py git-for-all tmp.ini checkout 2017.02~~
    RE=YES ./authors.sh tmp.ini process-repo
    python3 rel.py 3 tmp.ini
    python3 rel.py 6 tmp.ini
    python3 rel.py print-bibtex tmp.ini
    
<!-- OLD NOTES -->

# Release Model: how the 2016.06 release was done

Generally, the complete release is a two step process:

- branch and build on each lesson, pushing the changes
- create a folder and submodules, on the swc-releases

Both steps are currently semi-automated.
Some more details on these two steps are given here.

## Preparing all lessons for the release

This step has been automated by a bash function defined in `tools-for-lesson-maintainers.sh` (swc-releases repository) and that has been run with:

    . tools-for-lesson-maintainers.sh
    do-2016-06-from-gvwilson-list

This function will do the following for each lesson, e.g., for git-novice with version 2016.06:

- clone the repository as ,,git-novice if not already present (warning: one might need to remove the folder if changes have been push to github since the checkout)
- create a new branch 2016.06 from the latest gh-pages version (see NB)
- build the lesson, setting the Jekyll path to work on the swc-releases site
- copy the files that were just built and commit them
- patch the css to show the version number and commit it
- push the new branch

NB: WARNING: 2016.06: the `workshop-template` and `lesson-example` should use tags (the script does use branches as of 2016.06) as `import.github.com` does not play well enough with multiple branches. (this warning can be remove if the script is modified to handle this special cases).

NB: the two commits are prefixed with the DOI of the lesson.

NB: one need push access rights to all repositories to do that. The alternative is to have individual lesson maintainers do these steps.

The function can be copied and adapted for another new release.


## Populating the swc-releases repository

This step has been automated and live in this repository, where the main entry point is the Makefile.
To make the release, the following commands has been run:

    make 2016.06
    git commit -m 'Release 2016.06'
    git push

To be able to run this, the following preparation has been necessary:

- modify the Makefile to add the 2016.06 entry, and creating `CORE_LESSONS_B` (necessary only when the list of lessons changed)

When run, `make 2016.06` will run `make-or-update-release.sh` that will do the following:

- create a `2016.06` folder
- adding in this folder, one submodule per lesson (that tracks the `2016.06` branch of the lesson repository)
- generating an (ugly) HTML page `2016.06/index.html`
- adding everything so it is ready to commit
- encouraging the user to git commit and push



# About lessons using R (and RMarkdown in .rmd files)

One need to install R and some packages to build the lessons.

Installing R is platform dependent, e.g., under some linux distributions you can use `apt-get install r-base`.

One can then install the necessary packages by starting R and running:

    install.packages("knitr")
    install.packages("tidyr")
    install.packages("dplyr")
    install.packages("plyr")
    install.packages("DiagrammeR")
    install.packages("ggplot2")
    install.packages("devtools")
    install.packages("roxygen2")
    install.packages("checkpoint")



# Troubleshooting and help when having to do a release multiple times

## help with preparing lessons

In case the preparation process needs to be re-run, for instance because the build process need to be tuned, one may use the following tools (some functions are defined in `tools-for-lesson-maintainers.sh`).

- `rm -rf ,,*` to remove all checked out lessons: this can be useful if some changes, that needs to be integrated has been pushed on github since the clone
- `do-reset-,,-to-ghpages` to switch all checked out lesson repositories to the gh-pages branch (in case we want to rerun the script and that the script checks the current state of the repo, as done by the commented-out `do-check-justmerged` in do-2016-06-from-gvwilson-list)

## help with populating swc-releases

- `make check-submodules` to check that the revisions that submodules reference still exist on github (an absence causes Jekyll build issues)
- `rm -rf 2016.06` and `make clean-failure` to remove the generated folder and submodules
- IMPORTANT: also `rm -rf .git/modules/2016.06` to remove the submodule cache, in case some content has been force pushed to the lessons
- `git rebase -i HEAD^^` and later `git push --force` to rewrite history with a new version
- `make update-submodules` after uncommenting the necessary line in the Makefile: to update the submodules if new commits have been added to the 2016.06 branches in any lesson repository (need to then add/commit/push)




<!-- old stuff, more detailed but not totally in line with the fact that we now use Jekyll -->

# (old, still somewhat meaningful) Tentative Instructions for post bbq release

These instructions should help doing the release.
An informed release maintainer can also look at `tools-for-lesson-maintainers.sh` that contains script snippets that aim at automating the process.

## Step 1: Lesson Maintainers

NB: the HTML pages can be built before (on the gh-pages branch) or after (only in the release branch).

IMPORTANT: your pandoc version may matter for building the pages, see this thread <http://lists.software-carpentry.org/pipermail/discuss/2016-June/004553.html> (1.12 seems to not be fine with some source files, even if you don't see any errors when building) (some code blocks don't have newlines, classes are missing, etc)

You should already be on the gh-pages branch, but, if not, switch to it:

    git checkout gh-pages

Once the lesson (it's main gh-pages branch) is in a state to be release, the first step is to create a new branch that will be named `2016.06-beta`.

    git checkout -b 2016.06-beta
    # (use -B if you need to start over and force the re-creation of the branch)

If the HTML pages were not built yet, do it now and commit with a relevant message, the commands might look like this:

    # example to build the HTML pages and commit
    make clean preview
    git add *.html
    git status
    git commit -m "Rebuilt HTML files for release 2016.06-beta"

Then we will patch the css, so that the version is displayed on all pages.
Open the `css/swc.css` file and add, at the end, the following block (including the comments):

```{css}
/* version added automatically */
div.banner::before {
    content: "Version 2016.06-beta";
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
```

Then commit this change with:

    git add css/swc.css
    git commit -m "Added version (2016.06-beta) to all pages via CSS"

Then push the branch:

    git push --set-upstream origin 2016.06-beta
    # use --force if you had already pushed the branch and started over

And you can switch back to the main branch:

    git checkout gh-pages


## Step 2: Release Maintainer

Once all maintainers have created their branches, the release can be initiated.

The Makefile has already been prepared (if curious, look for 2016.06-beta inside), so you need to run:

    make 2016.06-beta
    # (and wait some time for the submodules to be added)

Then you can briefly review and commit:

    git status
    git commit -m "Release 2016.06-beta (after Bug BBQ)"

And finally push:

    git push

After letting some time to github to rebuild the site, you should see the release at <http://swcarpentry.github.io/swc-releases/2016.06-beta/> and each lessons should "work" and have a small banner with the version.
