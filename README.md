# swc-releases
Container for Software Carpentry lesson releases

- <http://swcarpentry.github.io/swc-releases/2015.08/> (5.3)
- <http://swcarpentry.github.io/swc-releases/2016.06-alpha/> (pre-bbq)





# Tentative Instructions for post bbq release

These instructions should help doing the release.
An informed release maintainer can also look at `tools-for-lesson-maintainers.sh` that contains script snippets that aim at automating the process.

## Step 1: Lesson Maintainers

NB: the HTML pages can be built before (on the gh-pages branch) or after (only in the release branch).

NB: your pandoc version may matter for building the pages, see this thread <http://lists.software-carpentry.org/pipermail/discuss/2016-June/004553.html>

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
