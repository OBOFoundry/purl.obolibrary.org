#!/usr/bin/env python3
#
# Reads a YAML file with a `term_browser` entry
# and an `example_terms` list,
# and writes Apache mod_alias RedirectMatch directives. See:
#
# https://httpd.apache.org/docs/2.4/mod/mod_alias.html
#
# The order of YAML objects will be the order
# of the Apache directives.
# If no example_terms are found, no output is generated.
#
# Note: currently works only for `term_browser: ontobee`.
# When `term_browser: custom` no output is generated.

import argparse, sys, yaml, re

header_template = '''# Term redirect for %s
'''

# Parse command line arguments,
# read entries from the YAML file,
# and write the Apache .htaccess file.
def main():
  parser = argparse.ArgumentParser(description='Translate YAML `example_terms` to .htaccess')
  parser.add_argument('yaml_file',
      type=argparse.FileType('r'),
      default=sys.stdin,
      nargs='?',
      help='read from the YAML file (or STDIN)')
  parser.add_argument('htaccess_file',
      type=argparse.FileType('w'),
      default=sys.stdout,
      nargs='?',
      help='write to the .htaccess file (or STDOUT)')
  args = parser.parse_args()

  # Load YAML document and look for 'entries' list.
  document = yaml.load(args.yaml_file)

  if not 'idspace' in document \
      or type(document['idspace']) is not str:
    raise ValueError('YAML document must contain "idspace" string')
  idspace = document['idspace']

  if 'term_browser' in document and document['term_browser'].strip().lower() == 'ontobee':
    args.htaccess_file.write(header_template % idspace)
    replacement = 'http://www.ontobee.org/browser/rdf.php?o=%s&iri=http://purl.obolibrary.org/obo/%s_$1' % (idspace, idspace)
    directive = 'RedirectMatch temp "^/obo/%s_(\d+)$" "%s"' % (idspace, replacement)
    args.htaccess_file.write(directive +'\n\n')


if __name__ == "__main__":
    main()
