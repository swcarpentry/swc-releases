
# Do not modify the following variables.
# If the set of core lessons changes, please add a new variable
CORE_LESSONS_A=shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation

# r-novice-gapminder matlab-novice-inflammation make-novice instructor-training

.PHONY: 2015.08

2015.08:
	TAG=v5.3 ./make-or-update-release.sh $@ ${CORE_LESSONS_A}


# can be useful (especially for development) if a release fails, you delete the subfolder and want to also delete the added submodules etc.
clean-failure:
	git rm $$(git ls-files -d)
