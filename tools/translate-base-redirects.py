#!/usr/bin/env python3
#
# Reads a YAML file with a `base_redirect` field
# and writes Apache mod_alias RedirectMatch directives. See:
#
# https://httpd.apache.org/docs/2.4/mod/mod_alias.html
#
# If the YAML file does not contain `base_redirect`,
# then no output is generated.

import argparse, sys, yaml, re

header_template = '''# Base redirect for %s
'''

# Parse command line arguments,
# read entries from the YAML file,
# and write the Apache .htaccess file.
def main():
  parser = argparse.ArgumentParser(description='Translate YAML `base_redirect` to .htaccess')
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

  if not 'base_url' in document \
      or type(document['base_url']) is not str:
    raise ValueError('YAML document must contain "base_url" string')
  base_url = document['base_url']

  if 'base_redirect' in document and type(document['base_redirect']) is str:
    args.htaccess_file.write(header_template % idspace)
    directive = 'RedirectMatch temp "^%s$" "%s"' % (base_url, document['base_redirect'])
    args.htaccess_file.write(directive + '\n\n')


if __name__ == "__main__":
    main()
