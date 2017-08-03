
# Do not modify the following variables.
# If the set of core lessons changes, please add a new variable
CORE_LESSONS_A=shell-novice git-novice hg-novice sql-novice-survey python-novice-inflammation r-novice-inflammation
CORE_LESSONS_B=git-novice hg-novice make-novice matlab-novice-inflammation python-novice-inflammation r-novice-gapminder r-novice-inflammation shell-novice sql-novice-survey lesson-example instructor-training workshop-template
CORE_LESSONS_C=git-novice hg-novice make-novice matlab-novice-inflammation python-novice-inflammation r-novice-gapminder r-novice-inflammation shell-novice sql-novice-survey lesson-example workshop-template

# r-novice-gapminder matlab-novice-inflammation make-novice instructor-training

.PHONY: 2015.08 2016.06-alpha 2016.06 2017.02 2017.08

nothing:
	@echo "An target should be explicitly specified."

2015.08:
	./make-or-update-release.sh $@ ${CORE_LESSONS_A}

2016.06-alpha:
	./make-or-update-release.sh $@ ${CORE_LESSONS_A}

2016.06:
	./make-or-update-release.sh $@ ${CORE_LESSONS_B}

2017.02:
	./make-or-update-release.sh $@ ${CORE_LESSONS_B}

2017.08:
	./make-or-update-release.sh $@ ${CORE_LESSONS_C}

update-submodules:
	#git submodule update --remote -- 2015.08/*/
	#git submodule update --remote -- 2016.06-alpha/*/
	#git submodule update --remote -- 2016.06/*/
	#git submodule update --remote -- 2017.02/*/
	git submodule update --remote -- 2017.08/*/

check-submodules:
	./check-submodules.sh

# can be useful (especially for development) if a release fails, you delete the subfolder and want to also delete the added submodules etc.
clean-failure:
	@echo "To do a full clean, you might also need to delete some things in .git/modules/"
	git rm $$(git ls-files -d)
