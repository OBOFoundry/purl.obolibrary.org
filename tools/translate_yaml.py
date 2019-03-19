#!/usr/bin/env python3

"""
Reads either a list of YAML files, or a directory containing YAML files,
and writes Apache mod_alias RedirectMatch directives to corresponding
.htaccess files. See:

https://httpd.apache.org/docs/2.4/mod/mod_alias.html

The `foo.yml` file will generate output for two targets:

1. /www/obo/foo/.htaccess
2. /www/obo/.htaccess

Target (1) only applies to project `foo`.
It is generated from `base_url` and the `entries` list.
Projects have wide discretion for this target.

Target (2) applies to all projects.
The content is tightly constrained to avoid conflicts.
This content is generated from other YAML fields,
such as `products` and `term_browser`.

Entries:
=======

There are three types of entries:

- exact: match an exact URL string
  and redirect to an exact URL
- prefix: match a URL prefix string,
  from the start of the request URL,
  and redirect to the "replacement" field plus
  any string following the prefix in the request
- regex: use any regular expression
  allowed by RedirectMatch

Entries can have these fields:

- exact/prefix/regex: the URL string or regex to match;
  exactly one required;
  should begin with a slash "/" except for some regexs
- replacement: the URL string or regex to redirect to;
  exactly one required
- status: HTTP status for redirect;
  zero or one value; defaults to "temporary";
  can be "permanent" (301), "temporary" (302), or "see other" (303);
  (Apache uses "temp" for "temporary")
- tests: an optional list of tests
  each test requires a `from` value, like `exact`,
  and a `to` value, like `replacement`

See the `tools/config.schema.json` for more details.

For the "exact" and "prefix" types,
the URL strings are rewritten as escaped regular expressions,
with a "^base_url" prefix and a "$" suffix.
Any regular expression special characters (e.g. ., *, ?, [])
will be escaped: they will not match as regular expressions.

For the "prefix" type, "(.*)" is also appended to the "prefix" field
and "$1" is appended to the "to" field,
to configure the prefix match.

For the "regex" type, the "" and "to" fields
are assumed to be valid regular expressions,
**including** the `base_url`,
and are not checked or modified.

**Only** use "regex" if "exact" or "prefix" are insufficient.

The order of YAML objects will be the order
of the Apache directives.
If no entries are found,
the generated file will have a header comment
without any directives.

Base redirects, Products, and Terms
===================================

These fields are optional. If the YAML input does not contain them, no
corresponding output will be generated.

Note that in the case of terms, only `term_browser: ontobee` is currently
supported. When `term_browser: custom` is used no output is generated.
"""

import functools
import json
import jsonschema
import re
import os
import sys
import yaml

from argparse import ArgumentParser
from glob import glob
from urllib.parse import unquote

pwd = os.path.dirname(os.path.realpath(__file__))
schemafile = "{}/config.schema.json".format(pwd)


def load_and_validate(yamlname, schema):
  try:
    yamlfile = open(yamlname)
    yamldoc = yaml.load(yamlfile)
    jsonschema.validate(yamldoc, schema)
  except (FileNotFoundError, IsADirectoryError, yaml.YAMLError) as e:
    print(e, file=sys.stderr)
    sys.exit(1)
  except jsonschema.exceptions.ValidationError as e:
    print("In file: {}:\n{}".format(yamlname, e), file=sys.stderr)
    sys.exit(1)

  # The following two errors should not occur, since the presence of `base_url` and `idspace`
  # should have been enforced by the above jsonschema validation step. But we double-check anyway.
  if 'base_url' not in yamldoc \
     or type(yamldoc['base_url']) is not str:
    print('YAML document must contain "base_url" string', file=sys.stderr)
    sys.exit(1)

  if 'idspace' not in yamldoc \
     or type(yamldoc['idspace']) is not str:
    print('YAML document must contain "idspace" string', file=sys.stderr)
    sys.exit(1)

  # jsonschema is not sophisticated enough to validate this one, so we do it here:
  if os.path.basename(yamldoc['base_url']).lower() != yamldoc['idspace'].lower():
    print("WARNING: Base URL '{}' must end with '{}', not '{}'"
          .format(yamldoc['base_url'], yamldoc['idspace'], os.path.basename(yamldoc['base_url'])))

  return yamldoc


def clean_source(s):
  """
  Given a URL string,
  return an escaped regular expression for matching that string.
  Only forward-slashes are not escaped.
  """
  r = s.strip()
  r = re.escape(r)
  r = r.replace('\\/', '/')
  return r


def process_entry(base_url, i, entry):
  """
  Given a base URL, an index, and an entry dictionary,
  ensure that the entry is valid,
  and return an Apache RedirectMatch directive string.
  """
  source = ''
  replacement = ''

  # Check entry data type
  if type(entry) is not dict:
    raise ValueError('Entry %d is not a YAML map: "%s"' % (i, entry))

  # Validate that "replacement" field exists. If it is missing it should have been caught by the
  # jsonschema validation step (see above), but we double-check anyway:
  if 'replacement' not in entry \
     or entry['replacement'] is None \
     or entry['replacement'].strip() == '':
    raise ValueError('Missing "replacement" field for entry %d' % i)

  # Determine the type for this entry.
  types = []
  if 'exact' in entry:
    source = '(?i)^%s%s$' % (base_url, clean_source(entry['exact']))
    replacement = entry['replacement']
    types.append('exact')
  if 'prefix' in entry:
    source = '(?i)^%s%s(.*)$' % (base_url, clean_source(entry['prefix']))
    replacement = entry['replacement'] + '$1'
    types.append('prefix')
  if 'regex' in entry:
    source = entry['regex']
    replacement = entry['replacement']
    types.append('regex')

  # Ensure that there is exactly one "type" key.
  if len(types) < 1:
    raise ValueError('Entry %d does not have a type; see "replacement: %s"'
                     % (i, entry['replacement']))
  elif len(types) > 1:
    raise ValueError('Entry %d has multiple types: %s; see "replacement: %s"'
                     % (i, ', '.join(types), entry['replacement']))

  # Validate status code. Any error here should have been caught by the jsonschema validation
  # (see above), but we double-check here anyway:
  status = 'temporary'
  if 'status' in entry:
    if entry['status'] in ('permanent', 'temporary', 'see other'):
      status = entry['status']
    else:
      raise ValueError('Invalid status "%s" for entry %d' % (entry['status'], i))

  # Switch to Apache's preferred names
  if status == 'temporary':
    status = 'temp'
  elif status == 'see other':
    status = 'seeother'

  source = unquote(source)
  replacement = unquote(replacement)

  return 'RedirectMatch %s "%s" "%s"' % (status, source, replacement)


def translate_entries(yamldoc, base_url):
  """
  Reads the field `entries` from the YAML document, processes each entry that is read using the
  given base_url, and appends them all to a list of processed entries that is then returned.
  """
  if 'entries' in yamldoc and type(yamldoc['entries']) is list:
    entries = []
    for i, entry in enumerate(yamldoc['entries']):
      entries.append(process_entry(base_url, i, entry))
    return entries


def write_entries(entries, yamlname, outfile):
  """
  Write the given entries to the given output stream, indicating the source YAML file
  from which the entries were extracted. Note that it is assumed that the output stream,
  `outfile` is open for writing.
  """
  outfile.write('# DO NOT EDIT THIS FILE!\n'
                '# Automatically generated from "%s".\n'
                '# Edit that source file then regenerate this file.\n\n'
                % yamlname)
  for entry in entries or []:
    outfile.write('{}\n'.format(entry))


def translate_base_redirects(yamldoc):
  """
  Reads the fields `base_redirect` and `base_url` from the given YAML document and
  generates a corresponding Apache directive string that is then returned.
  """
  if 'base_redirect' in yamldoc and type(yamldoc['base_redirect']) is str:
    base_url = unquote(yamldoc['base_url'])
    base_redirect = unquote(yamldoc['base_redirect'])
    directive = 'RedirectMatch temp "(?i)^%s$" "%s"' % (base_url, base_redirect)
    return directive


def append_base_redirect(base_redirect, idspace, outfile):
  """
  Appends the given base_redirect string for the given idspace to the given output stream.
  """
  if base_redirect:
    outfile.write('# Base redirect for %s\n' % idspace)
    outfile.write(base_redirect + '\n\n')


def process_product(product):
  """
  Given a product dictionary with one key,
  ensure that the entry is valid,
  and return an Apache RedirectMatch directive string.
  """
  key = [k for k in product].pop()
  source = unquote('(?i)^/obo/%s$' % key)
  replacement = unquote(product[key])
  return 'RedirectMatch temp "%s" "%s"' % (source, replacement)


def translate_products(yamldoc):
  """
  Reads the `products` field from the given YAML document, processes each product that is read,
  and appends them all to a list of processed products that is then returned.
  """
  if 'products' in yamldoc and type(yamldoc['products']) is list:
    products_have_owl = False
    products = []
    for product in yamldoc['products']:
      key = [k for k in product].pop()
      if not (key.lower().endswith('.owl') or key.lower().endswith('.obo')):
        # If we want to enforce this condition, the way to do it is to add
        # `"additionalProperties": false` right after `patternProperties` in the schema file.
        print("WARNING: In project '{}', product: '{}' does not end with '.owl' or '.obo'"
              .format(yamldoc['idspace'], key))
      if key.endswith('.owl'):
        products_have_owl = True

      products.append(process_product(product))

    if not products_have_owl:
      print("WARNING: In project '{}': Mandatory .owl entry missing from product list."
            .format(yamldoc['idspace']))

    return products


def append_products(products, idspace, outfile):
  """
  Appends the given list of products for the given idspace to the given output stream. Note that it
  it is assumed that the output stream `outfile` is open for appending.
  """
  if products:
    outfile.write('# Products for %s\n' % idspace)
    for product in products:
      outfile.write(product + '\n')
    outfile.write('\n')


def translate_terms(yamldoc, idspace):
  """
  Reads the `term_browser` field from the given YAML document, validates that it is a supported
  term browser, and returns a corresponding Apache redirect statement.
  """
  if 'term_browser' in yamldoc and yamldoc['term_browser'].strip().lower() == 'ontobee':
    replacement = ('http://www.ontobee.org/browser/rdf.php?'
                   'o=%s&iri=http://purl.obolibrary.org/obo/%s_$1'
                   % (idspace, idspace))
    return 'RedirectMatch seeother "^/obo/%s_(\d+)$" "%s"' % (idspace, replacement)


def append_term(term, idspace, outfile):
  """
  Appends the given term for the given idspace to the given output stream. Note that it is
  assumed that the output stream `outfile` is open for appending.
  """
  if term:
    outfile.write('# Term redirect for %s\n' % idspace)
    outfile.write(term + '\n\n')


# Parse command line arguments,
# read entries from the YAML file,
# and write the Apache .htaccess files.
def main():
  parser = ArgumentParser(description='''
  Translates YAML files to .htaccess.

  If a list of input YAML files is specified, then a .htaccess file is generated
  corresponding to each given YAML file, containing the `entries` specified in the
  YAML file. If a directory containing YAML files is specified instead, then in
  addition, the base redirects, terms, and products specified in the YAML file of
  each project will be appended to the top-level obo/.htaccess file in the given
  output directory.''')

  # This option is required:
  parser.add_argument('--output_dir', metavar='DIR', type=str, required=True,
                      help='Root directory to write to for project-specific .htaccess files')
  # The following options cannot be used simultaneously, but one of them needs to be specified:
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--input_files', metavar='YML', type=str, nargs='+',
                     help='List of YAML input files')
  group.add_argument('--input_dir', metavar='DIR', type=str,
                     help='Directory containing YAML input files')
  args = parser.parse_args()

  # Create the output directory, if it does not already exist. If this isn't possible, fail. Note
  # that if the directory already exists, then the files inside will be overwritten.
  normalised_output_dir = os.path.normpath(args.output_dir)
  try:
    os.makedirs(normalised_output_dir)
  except FileExistsError:
    pass

  schema = json.load(open(schemafile))
  entries = {}
  base_redirects = {}
  products = {}
  terms = {}
  if args.input_files:
    # If only a sequence of YAML filenames is given, then just write the entries found within
    # those files but not the base redirects, products, or terms.
    for yamlname in args.input_files:
      yamldoc = load_and_validate(yamlname, schema)
      base_url = yamldoc['base_url']
      # Extract the entries for the project from the YAML file:
      entries = translate_entries(yamldoc, base_url)
      # Write the entries for the given project to its project-specific .htaccess file, located
      # in a subdirectory under the given output directory. Note that if the subdirectory already
      # exists, the files inside will simply be overriden:
      yamlroot = re.sub('\.yml$', '', os.path.basename(yamlname))
      try:
        os.mkdir('{}/{}'.format(normalised_output_dir, yamlroot))
      except FileExistsError:
        pass
      with open('{}/{}/.htaccess'.format(normalised_output_dir, yamlroot), 'w') as outfile:
        write_entries(entries, yamlname, outfile)
  elif args.input_dir:
    if not os.path.isdir(args.input_dir):
      print("{} is not a directory.".format(args.input_dir))
      sys.exit(1)

    @functools.cmp_to_key
    def cmp(s, t):
      "Case-insensitive sort, longer names first"
      s = s.lower()
      t = t.lower()
      s_pad = (s + t[len(s):] + 'z') if len(s) < len(t) else s
      t_pad = (t + s[len(t):] + 'z') if len(t) < len(s) else t
      if s_pad < t_pad:
        return -1
      if s_pad > t_pad:
        return 1
      return 0

    normalised_input_dir = os.path.normpath(args.input_dir)
    for yamlname in sorted(glob("{}/*.yml".format(normalised_input_dir)), key=cmp):
      yamldoc = load_and_validate(yamlname, schema)
      base_url = yamldoc['base_url']
      # `idspace` and `yamlroot` are synonyms. The former is taken from the `idspace` specified
      # within the given YAML file, while the latter is derived from the filename. They need to
      # match (up to a change of case - idspace is always uppercase while yamlroot is lower).
      # If they do not match, emit a warning.
      idspace = yamldoc['idspace']
      yamlroot = re.sub('\.yml$', '', os.path.basename(yamlname))
      if idspace.lower() != yamlroot.lower():
        print("WARNING: idspace: {} does not match filename {}".format(idspace, yamlname))

      # Collect the entries for the current idspace:
      entries[idspace] = translate_entries(yamldoc, base_url)
      # Write the entries to the idspace's project-specific file located in its own subdirectory
      # under the output directory, as well as a symlink to the project subdirectory in the
      # output directory. If the files/directories already exist, they will be overwritten.
      try:
        projdir = '{}/{}'.format(normalised_output_dir, yamlroot)
        symlink = '{}/{}'.format(normalised_output_dir, idspace)
        os.mkdir(projdir)
        os.symlink(os.path.basename(projdir), symlink, target_is_directory=True)
      except FileExistsError:
        pass
      with open('{}/{}/.htaccess'.format(normalised_output_dir, yamlroot), 'w') as outfile:
        write_entries(entries[idspace], yamlname, outfile)

      # Extract the idspace's base redirects, products, and terms but do not write them yet:
      base_redirects[idspace] = translate_base_redirects(yamldoc)
      products[idspace] = translate_products(yamldoc)
      terms[idspace] = translate_terms(yamldoc, idspace)

    # Now write the entries for the 'OBO' idspace to a global .htaccess file located at the top
    # level of the output directory:
    with open('{}/.htaccess'.format(normalised_output_dir), 'w') as outfile:
      write_entries(entries['OBO'], '{}/obo.yml'.format(normalised_input_dir), outfile)

    # Append the base redirects, products, and terms to the global .htaccess file:
    with open('{}/.htaccess'.format(normalised_output_dir), 'a') as outfile:
      outfile.write('\n### Generated from project configuration files\n\n')
      for idspace in sorted(base_redirects, key=cmp):
        append_base_redirect(base_redirects[idspace], idspace, outfile)
      for idspace in sorted(products, key=cmp):
        append_products(products[idspace], idspace, outfile)
      for idspace in sorted(terms, key=cmp):
        append_term(terms[idspace], idspace, outfile)


if __name__ == "__main__":
    main()
