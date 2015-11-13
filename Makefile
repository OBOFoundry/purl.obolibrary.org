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


### Basic Operations

# Default goal: Remove generated files, validate config, and regenerate.
all: clean validate build

# Remove directories with generated files.
clean:
	rm -rf tests www/obo

# Generate .htaccess files for all YAML configuration files.
build: www/obo


### Configuration
#
# You can override these defaults with environment variables:
#
#     export DEVELOPMENT=172.16.100.10; make all test
#

# Local development server.
DEVELOPMENT ?= localhost

# Production server.
PRODUCTION ?= purl.obolibrary.org

# Do not automatically delete intermediate files.
.SECONDARY:

# These goals do not correspond to files.
.PHONY: all clean validate test test-production migrate-%


### Validate YAML Config
#
# Use kwalify and the tools/config.schema.yml
# to validate all YAML configuration files.
# If any INVALID results are found, exit with an error.
validate:
	kwalify -f tools/config.schema.yml config/*.yml \
	| awk '{print} /INVALID/ {status=1} END {exit $$status}'


### Generate Apache Config
#
# Convert the YAML configuration files
# to Apache .htaccess files with RedirectMatch directives.
www/obo/%/.htaccess: config/%.yml
	mkdir -p www/obo/$*
	tools/translate.py $< $@

# Convert all YAML configuration files to .htaccess
# and move the special `obo` .htaccess file.
www/obo: $(patsubst config/%.yml,www/obo/%/.htaccess,$(wildcard config/*.yml))
	mv www/obo/obo/.htaccess www/obo/.htaccess
	rm -rf www/obo/obo


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
test: $(patsubst config/%.yml,tests/development/%.tsv,$(wildcard config/*.yml))
	@cat tests/development/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit $$status}'


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
test-production: $(patsubst config/%.yml,tests/production/%.tsv,$(wildcard config/*.yml))
	@cat tests/production/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit $$status}'


### Test Tools
#
# Test our tools on files in examples/ directory.
tests/examples:
	mkdir -p $@

tests/examples/%.yml: tools/examples/%.xml tools/examples/%.yml tests/examples
	tools/migrate.py /obo/$* $< $@
	diff tools/examples/$*.yml $@

tests/examples/%.htaccess: tools/examples/%.yml tools/examples/%.htaccess tests/examples
	tools/translate.py $< $@
	diff tools/examples/$*.htaccess $@

test-examples: tests/examples/test1.yml tests/examples/test1.htaccess tests/examples/test2.htaccess


### Migrate Configuration from PURL.org
#
# Given an ontology ID (usually lower-case),
# fetch and translate a PURL.org XML file
# into a YAML configuration file.
# This should be a one-time migration.
# Do not overwrite existing config file.
PURL_XML = https://purl.org/admin/purl/?target=&seealso=&maintainers=&explicitmaintainers=&tombstone=false&p_id=

migrate-%:
	@test ! -s config/$*.yml \
	|| (echo 'Refusing to overwrite config/$*.yml'; exit 1)
	mkdir -p migrations
	test -s migrations/$*.xml \
	|| curl --fail -o migrations/$*.xml "$(PURL_XML)/obo/$*/*"
	mkdir -p config
	tools/migrate.py /obo/$* migrations/$*.xml config/$*.yml
