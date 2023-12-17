#!/usr/bin/make
PY_COV=python3-coverage
BROWSER=x-www-browser
PYTEST=pytest-3
OUT_DIR=output
SINGLE_TEST?=test_bom_ok
XMLS=tests/input_samples/

deb:
	fakeroot dpkg-buildpackage -uc -b

deb_clean:
	fakeroot debian/rules clean

lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --statistics

test_local: lint
#	No PyTest for Python 2 on bulleyes
#	rm -rf $(OUT_DIR)2
#	rm -f tests/input_samples/bom.ini
#	pytest --test_dir $(OUT_DIR)2
	rm -rf $(OUT_DIR)
	rm -f tests/input_samples/bom.ini
	$(PY_COV) erase
	${PYTEST} --test_dir $(OUT_DIR)
	$(PY_COV) report
	$(PY_COV) html
	$(BROWSER) htmlcov/index.html
	rm -f tests/input_samples/bom.ini

single_test:
	rm -rf pp
	-$(PYTEST) --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir pp
	@echo "********************" Output
	@cat pp/*/output.txt
	@echo "********************" Error
	@cat pp/*/error.txt
	@rm -f tests/input_samples/bom.ini

doc/Fork_PRs/examples/ds_link.html: doc/Fork_PRs/examples/ds_link.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

doc/Fork_PRs/examples/ds_no_link.html: doc/Fork_PRs/examples/ds_no_link.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

doc/Fork_PRs/examples/dk_link.html: doc/Fork_PRs/examples/dk_link.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

doc/Fork_PRs/examples/dk_no_link.html: doc/Fork_PRs/examples/dk_no_link.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

doc/Fork_PRs/examples/no_join.html: doc/Fork_PRs/examples/no_join.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)join.xml $(@F)

doc/Fork_PRs/examples/join.html: doc/Fork_PRs/examples/join.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)join.xml $(@F)

doc/Fork_PRs/examples/col_rename.html: doc/Fork_PRs/examples/col_rename.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

doc/Fork_PRs/examples/col_no_rename.html: doc/Fork_PRs/examples/col_no_rename.ini
	./KiBOM_CLI.py --cfg $< -d `pwd`/$(@D) $(XMLS)links.xml $(@F)

examples: doc/Fork_PRs/examples/ds_link.html doc/Fork_PRs/examples/ds_no_link.html \
	doc/Fork_PRs/examples/dk_link.html doc/Fork_PRs/examples/dk_no_link.html \
	doc/Fork_PRs/examples/no_join.html doc/Fork_PRs/examples/join.html \
	doc/Fork_PRs/examples/col_rename.html doc/Fork_PRs/examples/col_no_rename.html

.PHONY: deb deb_clean single_test test_local lint examples
