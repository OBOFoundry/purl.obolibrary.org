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
ONTOLOGY_IDS := bfo iao obi

# Use awk with tabs
AWK := awk -F "	" -v "OFS=	"

# Do not automatically delete intermediate files.
.SECONDARY:

# These goals do not correspond to files.
.PHONY: usage migrate-all all

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
# For 'partial' rules, append '(.*)' to the 'from' field
# and append '$1' to the 'to' field.
config/%.yml: migrate/%.xml config
	xmlstarlet sel \
	--template \
	--match '//purl' \
	--value-of 'type' --output '	' \
	--value-of 'id' --output '	' \
	--value-of 'target/url' --nl \
	$< \
	| sed 's!	/obo/$*/!	!' \
	| $(AWK) '$$1=="partial" {print $$1, $$2 "(.*)", $$3 "$$1"} \
	$$1!="partial" {print $$0}' \
	| $(AWK) '{print "- type: " $$1 "\n  from: " $$2 "\n  to: " $$3 "\n"}' \
	> $@


### Conversions
#
# Convert YAML to JSON for use with jq.
json:
	mkdir -p $@

json/%.json: config/%.yml json
	yaml2json < $< > $@


### Apache Config
#
# Convert the YAML configuration files
# to Apache .htaccess files with RewriteRules.

# Generate an .htaccess file from the configuration for an ontology.
# Use jq to grab `type`, `from`, and `to` fields
# and generate a Redirect or RedirectMatch rule.
# Redirect is for simple string matches.
# RedirectMatch uses regular expressions.
# See https://httpd.apache.org/docs/2.4/mod/mod_alias.html
www/obo/%/.htaccess: json/%.json
	mkdir -p www/obo/$*
	< $< \
	jq -r '.[] | \
	if (.type) == "partial" \
	then ["RedirectMatch ^", .from, "$$ ", .to] \
	else ["Redirect ", .type, " ", .from, " ", .to] \
	end \
	| map(tostring) | join("")' \
	> $@


### Other

all: clean $(foreach o,$(ONTOLOGY_IDS),www/obo/$o/.htaccess)

clean:
	rm -rf json www/obo/*

