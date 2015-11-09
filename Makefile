# OBO Purls Makefile
# 2015-11-06
# James A. Overton <james@overton.ca>
#
# This file contains code for working with
# Open Biomedical Ontoloiges (OBO)
# Persistent Uniform Resource Locators (PURLs).
#
# Required software:
#
# - yaml2json
# - [jq](https://stedolan.github.io/jq/)
# - [xmlstarlet](http://xmlstar.sourceforge.net) for migration from OCLC


### Configuration

# Run operations on these ontologies.
ONTOLOGY_IDS := obi

# Use awk with tabs
AWK := awk -F "	" -v "OFS=	"

# Do not automatically delete intermediate files.
.SECONDARY:

# These goals do not correspond to files.
.PHONY: usage migrate-all all clean

usage:
	@echo 'Usage: make all'


### Migrate
#
# Fetch and reformat code from OCLC in XML format
# and convert it to YAML format for further editing.

migrate:
	mkdir -p $@

OCLC_ADMIN := https://purl.org/admin/purl/

# Fetch first 100 PURLs for a given path from OCLC in XML format.
OCLC_XML = $(OCLC_ADMIN)?target=&seealso=&maintainers=&explicitmaintainers=&tombstone=false&p_id=

# Fetch all OCLC PURLs for given ontology ID.
migrate/%.xml: migrate
	sleep 5
	curl -o $@ "$(OCLC_XML)/obo/$*/*"

# Fetch XML for all ontologies in the ONTOLOGY_IDS list.
migrate-all: $(foreach o,$(ONTOLOGY_IDS),config/$o.yml)


config:
	mkdir -p $@

# Use xmlstarlet to convert XML to YAML format.
config/%.yml: migrate/%.xml config
	xmlstarlet sel \
	--template \
	--match '//purl' \
	--output '- from: ' --value-of 'id' --nl \
	--output '  to: '   --value-of 'target/url' --nl \
	--output '  type: ' --value-of 'type' --nl \
	--nl \
	$< \
	| sed 's!^\- from: /obo/$*!- from: !' \
	| sed '/^  type: 302$$/d' \
	| sed 's/^  type: partial$$/  type: prefix/' \
	> $@


### Apache Config
#
# Convert the YAML configuration files
# to Apache .htaccess files with RewriteRules.
obo/%/.htaccess: config/%.yml
	mkdir -p obo/$*
	./translate.py < $< > $@


### Other

all: clean $(foreach o,$(ONTOLOGY_IDS),obo/$o/.htaccess)

clean:
	rm -rf obo/obi

