#!/usr/bin/env python3
#
# Reads a YAML file with a list of `products`
# and writes Apache mod_alias RedirectMatch directives. See:
#
# https://httpd.apache.org/docs/2.4/mod/mod_alias.html
#
# The order of YAML objects will be the order
# of the Apache directives.
# If no products are found, no output is generated.

import argparse, sys, yaml, re

header_template = '''# Products for %s
'''

# Parse command line arguments,
# read entries from the YAML file,
# and write the Apache .htaccess file.
def main():
  parser = argparse.ArgumentParser(description='Translate YAML `products` to .htaccess')
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

  if 'products' in document and type(document['products']) is list:
    args.htaccess_file.write(header_template % document['id'])
    i = 0
    for product in document['products']:
      i += 1
      args.htaccess_file.write(process_product(i, product) + '\n')
    args.htaccess_file.write('\n')


def process_product(i, product):
  """Given an index, and a product dictionary with one key,
  ensure that the entry is valid,
  and return an Apache RedirectMatch directive string."""
  for key in product:
    source = '^/obo/%s$' % key
    replacement = product[key]

    return 'RedirectMatch temp "%s" "%s"' % (source, replacement)


if __name__ == "__main__":
    main()
