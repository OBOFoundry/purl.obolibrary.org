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


### Configuration

# Run operations on these ontologies.
ONTOLOGY_IDS := obi

# Default goal: Generate an .htaccess file for each id in ONTOLOGY_IDS.
all: clean validate build

build: www/obo

clean:
	rm -rf tests www/obo

# Use awk with tabs
AWK := awk -F "	" -v "OFS=	"

# Do not automatically delete intermediate files.
.SECONDARY:

# These goals do not correspond to files.
.PHONY: all clean validate test test-production fetch migrate migrate-%


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

# Convert the special global OBO configuration file.
www/obo/.htaccess: config/obo.yml
	mkdir -p www/obo
	tools/translate.py $< $@

# Convert configuration for all ontologies in ONTOLOGY_IDS.
www/obo: www/obo/.htaccess $(foreach o,$(ONTOLOGY_IDS),www/obo/$o/.htaccess)


### Test Development Apache Config
#
# Make HTTP HEAD requests against a local development server
# to ensure that redirects are working properly.
tests/development:
	mkdir -p $@

# Run tests for a single YAML configuration file.
# against the developmentelopment server,
# making requests every 0.01 seconds.
tests/development/%.tsv: config/%.yml tests/development
	tools/test.py --delay=0.01 172.16.100.10 $< $@

# Run all tests against development and fail if any FAIL line is found.
test: $(patsubst config/%.yml,tests/development/%.tsv,$(wildcard config/*.yml))
	@cat tests/development/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit $$status}'


### Test Production Apache Config
#
# Make HTTP HEAD requests against the production server
# to ensure that redirects are working properly.
tests/production:
	mkdir -p $@

# Run tests for a single YAML configuration file
# against the production server,
# making requests every 1 second.
tests/production/%.tsv: config/%.yml tests/production
	tools/test.py --delay=1 purl.obolibrary.org $< $@

# Run all tests against production and fail if any FAIL line is found.
test-production: $(patsubst config/%.yml,tests/production/%.tsv,$(wildcard config/*.yml))
	@cat tests/production/*.tsv \
	| awk '/^FAIL/ {status=1; print} END {exit $$status}'


### Fetch from OCLC
#
# Fetch records from OCLC in XML format.
migrations:
	mkdir -p $@

OCLC_XML = https://purl.org/admin/purl/?target=&seealso=&maintainers=&explicitmaintainers=&tombstone=false&p_id=

# Fetch first 100 PURLs for a given path from OCLC in XML format.
migrations/%.xml: migrations
	sleep 5
	curl -o $@ "$(OCLC_XML)/obo/$*/*"

# Fetch XML for all ontologies in the ONTOLOGY_IDS list.
fetch: $(foreach o,$(ONTOLOGY_IDS),migrations/$o.xml)


### Migrate Configuration from OCLC
#
# Translate OCLC XML files into YAML files.
# This should be a one-time migration.
# WARN: Don't overwrite newer configuration files!
config:
	mkdir -p $@

# Convert XML to YAML format.
# Do not overwrite existing config file.
migrate-%: migrations/%.xml config
	@test ! -s config/$*.yml \
	|| (echo 'Refusing to overwrite config/$*.yml') \
	&& tools/migrate.py /obo/$* migrations/$*.xml config/$*.yml

# Migrate XML to YAML for all ontologies in the ONTOLOGY_IDS list.
migrate: $(foreach o,$(ONTOLOGY_IDS),migrate-$o)

