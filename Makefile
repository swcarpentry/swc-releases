
# Do not modify the following variables.
# If the set of core lessons changes, please add a new variable
CORE_LESSONS_A=shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation
CORE_LESSONS_B=git-novice hg-novice make-novice matlab-novice-inflammation python-novice-inflammation r-novice-gapminder r-novice-inflammation shell-novice sql-novice-survey lesson-example instructor-training workshop-template

# r-novice-gapminder matlab-novice-inflammation make-novice instructor-training

.PHONY: 2015.08 2016.06-alpha 2016.06

nothing:
	@echo "An target should be explicitly specified."

2015.08:
	./make-or-update-release.sh $@ ${CORE_LESSONS_A}

2016.06-alpha:
	./make-or-update-release.sh $@ ${CORE_LESSONS_A}

2016.06:
	./make-or-update-release.sh $@ ${CORE_LESSONS_B}

update-submodules:
	#git submodule update --remote -- 2015.08/*
	#git submodule update --remote -- 2016.06-alpha/*
	#git submodule update --remote -- 2016.06/*


# can be useful (especially for development) if a release fails, you delete the subfolder and want to also delete the added submodules etc.
clean-failure:
	@echo "To do a full clean, you might also need to delete some things in .git/modules/"
	git rm $$(git ls-files -d)
