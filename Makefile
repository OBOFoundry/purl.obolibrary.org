# OBO Purls Makefile
# 2015-11-06
# James A. Overton <james@overton.ca>
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
# - [kwalify](http://www.kuwata-lab.com/kwalify/) for YAML validation
# - [Python 3](https://www.python.org/downloads/) to run scripts
# - [PyYAML](http://pyyaml.org/wiki/PyYAML) for translation to Apache
# - [travis.rb](https://github.com/travis-ci/travis.rb) for Travis-CI


### Configuration
#
# You can override these defaults with environment variables:
#
#     export DEVELOPMENT=172.16.100.10; make all test
#

# List of ontology IDs to work with, as file names (lowercase).
# Defaults to the list of config/*.yml files.
ONTOLOGY_IDS ?= $(patsubst config/%.yml,%,$(wildcard config/*.yml))

# The GitHub owner/project
PROJECT ?= OBOFoundry/purl.obolibrary.org

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

# Default goal: Remove generated files, validate config, and regenerate.
.PHONY: all
all: clean validate build

# Remove directories with generated files.
.PHONY: clean
clean:
	rm -rf temp tests


### Validate YAML Config
#
# Use kwalify and the tools/config.schema.yml
# to validate all YAML configuration files.
# If any INVALID results are found, exit with an error.
.PHONY: validate
validate:
	/usr/local/bin/kwalify -f tools/config.schema.yml config/*.yml \
	| awk '{print} /INVALID/ {status=1} END {exit status}'

# Validate a single configuration file.
.PHONY: validate-%
validate-%:
	/usr/local/bin/kwalify -f tools/config.schema.yml config/$*.yml


### Generate Apache Config
#
# Convert the YAML configuration files
# to Apache .htaccess files with RedirectMatch directives.
# There are three types:
#
# - base_redirects: when the project's base_url points to something
# - product: for a project's main OWL file
# - term: for a project's terms
# - entries: PURLs under the project's base_url
#
# The first three are inserted into www/obo/.htaccess
# while the last is in the project's www/obo/project/.htaccess
#
# These files are built in the `temp/` directory
# then `temp/obo` replaces `www/obo` as the very last step
# to keep Apache downtime to an absolute minimum.
temp/obo temp/base_redirects temp/products temp/terms:
	mkdir -p $@

temp/base_redirects/%.htaccess: config/%.yml temp/base_redirects
	tools/translate-base-redirects.py $< $@

temp/products/%.htaccess: config/%.yml temp/products
	tools/translate-products.py $< $@

temp/terms/%.htaccess: config/%.yml temp/terms
	tools/translate-terms.py $< $@

# Generate temp/obo/foo/.htaccess file
# and a symbolic link from the IDSPACE:
# temp/obo/FOO -> temp/obo/foo
# NOTE: The last line removes spurious links
# on case insensitive file systems such as Mac OS X.
temp/obo/%/.htaccess: config/%.yml
	mkdir -p temp/obo/$*
	tools/translate-entries.py $< $@
	< $< \
	grep '^idspace:' \
	| sed 's/^idspace://' \
	| tr -d ' ' \
	| awk '{print "$* temp/obo/" $$0}' \
	| xargs -t ln -s
	rm -f temp/obo/$*/$*

# Build temp files for a single project.
.PHONY: build-%
build-%: validate-% temp/obo/%/.htaccess temp/base_redirects/%.htaccess temp/products/%.htaccess temp/terms/%.htaccess
	@echo "Built files in temp/$*"

backup/:
	mkdir $@

# Get name of a dated-backup directory, in a portable way.
BACKUP = backup/obo-$(shell python -c "import time,os;print(time.strftime('%Y%m%d-%H%M%S',time.gmtime(os.path.getmtime('www/obo'))))")

# Convert all YAML configuration files to .htaccess
# and move the special `obo` .htaccess file.
# Generate .htaccess files for all YAML configuration files.
.PHONY: build
build: $(foreach o,$(ONTOLOGY_IDS),temp/obo/$o/.htaccess)
build: $(foreach o,$(ONTOLOGY_IDS),temp/base_redirects/$o.htaccess)
build: $(foreach o,$(ONTOLOGY_IDS),temp/products/$o.htaccess)
build: $(foreach o,$(ONTOLOGY_IDS),temp/terms/$o.htaccess)
build: | backup/
	cat temp/obo/obo/.htaccess > temp/obo/.htaccess
	echo '' >> temp/obo/.htaccess
	echo '### Generated from project configuration files' >> temp/obo/.htaccess
	echo '' >> temp/obo/.htaccess
	cat temp/base_redirects/*.htaccess >> temp/obo/.htaccess
	cat temp/products/*.htaccess >> temp/obo/.htaccess
	cat temp/terms/*.htaccess >> temp/obo/.htaccess
	rm -rf temp/obo/obo
	rm -rf temp/obo/OBO
	-test -e www/obo && mv www/obo $(BACKUP)
	mv temp/obo www/obo


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
tests/examples:
	mkdir -p $@

tests/examples/%.yml: tools/examples/%.xml tools/examples/%.yml tests/examples
	tools/migrate.py $* $< $@
	diff tools/examples/$*.yml $@

tests/examples/%.base_redirects.htaccess: tools/examples/%.yml tests/examples
	tools/translate-base-redirects.py $< $@
	diff tools/examples/$*.base_redirects.htaccess $@

tests/examples/%.products.htaccess: tools/examples/%.yml tests/examples
	tools/translate-products.py $< $@
	diff tools/examples/$*.products.htaccess $@

tests/examples/%.terms.htaccess: tools/examples/%.yml tests/examples
	tools/translate-terms.py $< $@
	diff tools/examples/$*.terms.htaccess $@

tests/examples/%.htaccess: tools/examples/%.yml tests/examples
	tools/translate-entries.py $< $@
	diff tools/examples/$*.htaccess $@

.PHONY: test-examples
test-examples: tests/examples/test1.yml
test-examples: tests/examples/test2.htaccess
test-examples: tests/examples/test2.base_redirects.htaccess
test-examples: tests/examples/test2.products.htaccess
test-examples: tests/examples/test2.terms.htaccess


### Update Repository
#
# Check Travis-CI for the last build.
# If it did not pass, then fail.
# If it is the same as .current_build, then fail.
# Otherwise replace .current_build,
# pull from git, and run a new `make`.
safe-update:
	travis history --no-interactive \
	--repo $(PROJECT) --branch master --limit 1 \
	> .travis_build
	@grep ' passed:   ' .travis_build
	@echo 'Last build is green, but might not be new'
	@diff .current_build .travis_build && exit 1 || exit 0
	@echo 'New green build available'
	@mv .travis_build .current_build
	git pull
	make


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
