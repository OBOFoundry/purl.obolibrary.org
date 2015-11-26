#!/usr/bin/env python3
#
# Migrate PURL configuration
# from a [PURL.org](http://purl.org) XML file
# to a YAML configuration file.
# This script is helpful, but manual improvements are required!
#
# Given the project ID, this tool will generate several required fields,
# then read the PURL.org XML to generate a list of rules.
#
# Each PURL is configured in a `<purl>` element, like this:
#
#     <purl status="1">
#       <id>/obo/obi/branches/</id>
#       <type>partial</type>
#       <maintainers><uid>ALANRUTTENBERG</uid></maintainers>
#       <target>
#         <url>http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/</url>
#       </target>
#     </purl>
#
# The result will be a YAML list of maps like this:
#
#     purl_rules:
#     - prefix: /obo/obi/branches/
#       replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/
#
# We use a SAX parser to efficiently read selected fields: id, type, url.
#
# PURLs with type "302" will be `path` rules.
# PURLs with type "partial" will be `prefix` rules.
# To ensure that PURL.org behaviour is duplicated by default,
# the `path` rules are output first,
# followed by `prefix` rules in descending order of `id` length.

import argparse, sys, xml.sax, re

# Accumulate rules in these global lists for later sorting.
path = []
prefix = []

# Define two template strings.
header_template = '''# PURL configuration for {idspace}

purl_rules:
- term_browser: ontobee
  tests:
  - path: /obo/{idspace}_0000001
    replacement: http://www.ontobee.org/browser/rdf.php?o={idspace}&iri=http://purl.obolibrary.org/obo/{idspace}_0000001

- path: /obo/{lower_idspace}.owl
  replacement: http://www.berkeleybop.org/ontologies/{lower_idspace}.owl

- path: /obo/{lower_idspace}.obo
  replacement: http://www.berkeleybop.org/ontologies/{lower_idspace}.obo

'''
rule_template = '''- {type}: {id}
  replacement: {url}

'''

# Parse command line arguments,
# run the SAX parser on the XML file,
# and write results to the YAML file.
def main():
  parser = argparse.ArgumentParser(description='Migrate XML to YAML')
  parser.add_argument('idspace',
      type=str,
      help='the project IDSPACE, e.g. FOO')
  parser.add_argument('xml_file',
      type=argparse.FileType('r'),
      default=sys.stdin,
      nargs='?',
      help='read from the XML file (or STDIN)')
  parser.add_argument('yaml_file',
      type=argparse.FileType('w'),
      default=sys.stdout,
      nargs='?',
      help='write to the YAML file (or STDOUT)')
  args = parser.parse_args()

  config = {
    'idspace': args.idspace,
    'lower_idspace': args.idspace.lower()
  }

  sax = xml.sax.make_parser()
  sax.setContentHandler(OCLCHandler())
  sax.parse(args.xml_file)

  rules = path + sorted(prefix, key=lambda k: len(k['id']), reverse=True)

  args.yaml_file.write(header_template.format(**config))
  for rule in rules:
    args.yaml_file.write(rule_template.format(**rule))


# Define a SAX ContentHandler class to match the XML format,
# and accumulate rule dictionaries into the global lists.
# See example above for XML format.
class OCLCHandler(xml.sax.ContentHandler):
  # Initialize with results of argparse.
  def __init__(self):
    self.count = 0
    self.content = ''
    self.rule = {}

  # If this is a new `<purl>` element, clear variables.
  # Always clear the content buffer.
  def startElement(self, name, attrs):
    self.content = ''
    if name == 'purl':
      self.count += 1
      self.rule = {}

  # Accumulate characters.
  def characters(self, content):
    self.content += content

  # Get the first value found for type, id, and url.
  # If this is the end of a `purl` element,
  # validate the rule dictionary,
  # then store it in one of the global lists.
  def endElement(self, name):
    if name in ('type', 'id', 'url'):
      if self.content.strip() == '':
        raise ValueError('Empty <%s> for <purl> %d' % (name, self.count))
      self.rule[name] = self.content.strip()

    elif name == 'purl':
      if not 'id' in self.rule:
        raise ValueError('No <id> for <purl> %d' % self.count)
      if not 'url' in self.rule:
        raise ValueError('No <url> for <purl> %d' % self.count)
      if not 'type' in self.rule:
        raise ValueError('No <type> for <purl> %d' % self.count)
      elif self.rule['type'] == '302':
        self.rule['type'] = 'path'
        path.append(self.rule)
      elif self.rule['type'] == 'partial':
        self.rule['type'] = 'prefix'
        prefix.append(self.rule)
      else:
        raise ValueError('Unknown type "%s" for <purl> %d' %
            (self.rule['type'], self.count))

if __name__ == "__main__":
    main()
