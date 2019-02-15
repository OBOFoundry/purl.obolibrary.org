# OBO Purls Makefile
# 2015-11-06
# James A. Overton <james@overton.ca>
#
# Last major modification: 2019-02-10, Michael Cuffaro <consulting@michaelcuffaro.com>
#
# This file contains code for working with
# Open Biomedical Ontoloiges (OBO)
# Persistent Uniform Resource Locators (PURLs).
#
# WARNING: This file contains significant whitespace!
# Make sure that your text editor distinguishes tabs from spaces.
#
# Required software:
#
# - [GNU Make](http://www.gnu.org/software/make/) to run this file
# - [Python 3](https://www.python.org/downloads/) to run scripts
# - [PyYAML](http://pyyaml.org/wiki/PyYAML) for translation to Apache


### Configuration
#
# You can override these defaults with environment variables:
#
#     export DEVELOPMENT=172.16.100.10; make all test
#

# List of ontology IDs to work with, as file names (lowercase).
# Defaults to the list of config/*.yml files.
ONTOLOGY_IDS ?= $(patsubst config/%.yml,%,$(wildcard config/*.yml))

# Local development server.
DEVELOPMENT ?= localhost

# Production server.
PRODUCTION ?= purl.obolibrary.org


### Boilerplate
#
# Recommended defaults: http://clarkgrubb.com/makefile-style-guide

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.SUFFIXES:


### Basic Operations

# Default goal: Remove generated files and regenerate.
.PHONY: all
all: clean build

# Remove directories with generated files and tests.
.PHONY: clean
clean:
	rm -rf temp tests

# Build temp files for a single project.
.PHONY: build-%
build-%:
	tools/translate_yaml.py --input_files config/$*.yml --output_dir temp
	@echo "Built files in temp/$*"

# The following two directories Must exist in order to execute the code that
# assigns the variable BACKUP (see below)
backup/:
	mkdir $@

www/obo/:
	mkdir -p $@

# Get name of a dated-backup directory, in a portable way.
BACKUP = backup/obo-$(shell python -c "import time,os;print(time.strftime('%Y%m%d-%H%M%S',time.gmtime(os.path.getmtime('www/obo'))))")

# Convert all YAML configuration files to .htaccess.
.PHONY: build
build: | backup/ www/obo/
	tools/translate_yaml.py --input_dir config --output_dir temp/obo
	rm -rf temp/obo/obo
	-test -e www/obo && mv www/obo $(BACKUP)
	mv temp/obo www/obo
	rmdir temp

### Test Development Apache Config
#
# Make HTTP HEAD requests quickly against the DEVELOPMENT server
# to ensure that redirects are working properly.
tests/development:
	mkdir -p $@

# Run tests for a single YAML configuration file.
# against the DEVELOPMENT server,
# making requests every 0.01 seconds.
tests/development/%.tsv: config/%.yml tests/development
	tools/test.py --delay=0.01 $(DEVELOPMENT) $< $@

# Run all tests against development and fail if any FAIL line is found.
.PHONY: test
test: $(foreach o,$(ONTOLOGY_IDS),tests/development/$o.tsv)
	@cat tests/development/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit status}'


### Test Production Apache Config
#
# Make HTTP HEAD requests slowly against the PRODUCTION server
# to ensure that redirects are working properly.
tests/production:
	mkdir -p $@

# Run tests for a single YAML configuration file
# against the PRODUCTION server,
# making requests every 1 second.
tests/production/%.tsv: config/%.yml tests/production
	tools/test.py --delay=1 $(PRODUCTION) $< $@

# Run all tests against production and fail if any FAIL line is found.
.PHONY: test-production
test-production: $(foreach o,$(ONTOLOGY_IDS),tests/production/$o.tsv)
	@cat tests/production/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit status}'


### Test Tools
#
# Test our tools on files in examples/ directory.
.PHONY: test-examples test-example1 test-example2
test-example1:
	tools/migrate.py test1 tools/examples/test1/test1.xml tests/examples/test1/test1.yml
	diff tools/examples/test1/test1.yml tests/examples/test1/test1.yml
test-example2:
	tools/translate_yaml.py --input_dir tools/examples/test2/ --output_dir tests/examples/test2/
	diff tools/examples/test2/test2.htaccess tests/examples/test2/.htaccess
	diff tools/examples/test2/obo/obo.htaccess tests/examples/test2/obo/.htaccess
	diff tools/examples/test2/test2/test2.htaccess tests/examples/test2/test2/.htaccess	
test-examples: test-example1 test-example2


### Update Repository
#
# Run the safe-update.py script which does the following:
# - Check Travis-CI for the last build.
# - If it did not pass, or if it is the same as the current build, then do nothing.
# - Otherwise replace .current_build, pull from git, and run a new `make`.
safe-update:
	tools/safe-update.py

### Migrate Configuration from PURL.org
#
# Given an ontology ID (usually lower-case),
# fetch and translate a PURL.org XML file
# into a YAML configuration file.
# This should be a one-time migration.
# Do not overwrite existing config file.
PURL_XML = https://purl.org/admin/purl/?target=&seealso=&maintainers=&explicitmaintainers=&tombstone=false&p_id=

.PHONY: migrate-%
migrate-%:
	@test ! -s config/$*.yml \
	|| (echo 'Refusing to overwrite config/$*.yml'; exit 1)
	mkdir -p migrations
	test -s migrations/$*.xml \
	|| curl --fail -o migrations/$*.xml "$(PURL_XML)/obo/$**"
	mkdir -p config
	tools/migrate.py $* migrations/$*.xml config/$*.yml

### Check code style for python source files.
# || true is appended to force make to ignore the exit code from pycodestyle
.PHONY: style
style:
	pep8 --max-line-length=100 --ignore E129,E126,E121,E111,E114 tools/*.py || true

# Run the delinter
lint:
	python3 -m pyflakes tools/*.py || true
