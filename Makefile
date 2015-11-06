# OBO Purls Makefile
# 2015-11-06
# James A. Overton <james@overton.ca>
#
# This file contains code for working with
# Open Biomedical Ontoloiges (OBO)
# Persistent Uniform Resource Locators (PURLs).
#
# Requires [xmlstarlet](http://xmlstar.sourceforge.net)


ONTOLOGY_IDS := bfo iao obi

.PHONY: migrate-all

### Migrate
#
# Fetch and reformat code from OCLC to a neutral format.

migrate:
	mkdir -p $@

OCLC_ADMIN := https://purl.org/admin/purl/

# Fetch first 100 PURLs for a given path from OCLC in XML format.
OCLC_XML = $(OCLC_ADMIN)?target=&seealso=&maintainers=&explicitmaintainers=&tombstone=false&p_id=

# Fetch all OCLC PURLs for given ontology ID.
migrate/%.xml: migrate
	sleep 5
	curl -o $@ "$(OCLC_XML)/obo/$*/*"

config:
	mkdir -p $@

# Use xmlstarlet to convert XML to text format.
# Each `purl` element becomes a row with three columns
# separated by spaces: type, id, url.
config/%.txt: migrate/%.xml config
	xmlstarlet sel \
	--template \
	--match '//purl' \
	--value-of 'type' --output ' ' \
	--value-of 'id' --output ' ' \
	--value-of 'target/url' --nl \
	$< \
	> $@


# Migrate and reformat all ontologies in ONTOLOGY_IDS.
migrate-all: $(foreach o,$(ONTOLOGY_IDS),config/$o.txt)


