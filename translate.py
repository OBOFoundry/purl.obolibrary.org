#!/usr/bin/env python3
#
# Reads a YAML list of objects from STDIN,
# and writes Apache mod_alias RedirectMatch directives
# to STDOUT. See:
#
# https://httpd.apache.org/docs/2.4/mod/mod_alias.html
#
# There are three types of rules:
#
# - exact: match an exact URL string
#   and redirect to an exact URL
# - prefix: match a URL prefix string,
#   from the start of the request URL,
#   and redirect to the "replacement" field plus
#   any string following the prefix in the request
# - regex: use any regular expression
#   allowed by RedirectMatch
#
# YAML objects can have these fields:
#
# - exact/prefix/regex: the URL string or regex to match;
#   exactly one required;
#   should begin with a slash "/" except for some regexs
# - replacement: the URL string or regex to redirect to;
#   exactly one required
# - status: HTTP status for redirect;
#   zero or one value; defaults to "temporary";
#   can be "permanent" (301) or "temporary" (302);
#   (Apache uses "temp" for "temporary")
#
# For the "exact" and "prefix" types,
# the URL strings are rewritten as escaped regular expressions,
# with "^" and "$" anchors.
# Any regular expression special characters (e.g. ., *, ?, [])
# will be escaped: they will not match as regular expressions.
#
# For the "prefix" type, "(.*)" is also appended to the "prefix" field
# and "$1" is appended to the "to" field,
# to configure the prefix match.
#
# For the "regex" type, the "" and "to" fields
# are assumed to be valid regular expressions,
# and are not checked or modified.
#
# Only use "regex" if "full" or "prefix" are insufficient.
#
# The order of YAML objects will be the order
# of the Apache directives.

import sys, yaml, re, urllib.parse

def clean_source(s):
  """Given a URL string,
  return an escaped regular expression for matching that string.
  Only forward-slashes are not escaped."""
  r = s.strip()
  r = urllib.parse.urlparse(r).geturl()
  r = re.escape(r)
  r = r.replace('\\/', '/')
  return r

def clean_replacement(s):
  """Given a URL string,
  return an escaped regular expression for matching that string."""
  return urllib.parse.urlparse(s.strip()).geturl()

# Load YAML document and look for 'entries' list.
document = yaml.load(sys.stdin)

if not 'entries' in document \
    or document['entries'] is None \
    or type(document['entries']) is not list:
  raise ValueError('Document must contain "entries" list')

# For each entry, validate it then generate a RedirectMatch directive.
i = 0
for entry in document['entries']:
  i += 1
  source = ''
  replacement = ''

  # Check entry data type
  if type(entry) is not dict:
    raise ValueError('Entry %d is invalid: "%s"' % (i, entry))

  # Validate "replacement" field
  if not 'replacement' in entry \
      or entry['replacement'] is None \
      or entry['replacement'].strip() == '':
    raise ValueError('Missing "replacement" field for entry %d' % i)

  # Determine the type for this entry.
  types = []
  if 'exact' in entry:
    source = '^%s$' % clean_source(entry['exact'])
    replacement = clean_replacement(entry['replacement'])
    types.append('exact')
  if 'prefix' in entry:
    source = '^%s(.*)$' % clean_source(entry['prefix'])
    replacement = clean_replacement(entry['replacement']) + '$1'
    types.append('prefix')
  if 'regex' in entry:
    source = entry['regex']
    replacement = entry['replacement']
    types.append('regex')

  # Ensure that there is no more than one "type" key.
  if len(types) < 1:
    raise ValueError('Entry %d does not have a type; see "replacement: %s"'
        % (i, entry['replacement']))
  elif len(types) > 1:
    raise ValueError('Entry %d has multiple types: %s; see "replacement: %s"'
        % (i, ', '.join(types), entry['replacement']))

  # Validate status code
  status = 'temporary'
  if 'status' in entry:
    if entry['status'] in ('temporary', 'permanent'):
      status = entry['status']
    else:
      raise ValueError('Invalid status "%s" for entry %d' % (entry['status'], i))

  # Note: Apache config uses "temp" instead of "temporary"
  if status == 'temporary':
    status = 'temp'

  print('RedirectMatch %s "%s" "%s"' % (status, source, replacement))

