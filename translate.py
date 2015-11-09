#!/usr/bin/env python3
#
# Reads a YAML array of objects from STDIN,
# and writes Apache mod_alias RedirectMatch directives
# to STDOUT. See:
#
# https://httpd.apache.org/docs/2.4/mod/mod_alias.html
#
# There are three types of rules:
#
# - full (default): match an exact URL string
#   and redirect to an exact URL
# - prefix: match a URL prefix string,
#   from the start of the request URL,
#   and redirect to the "to" field plus
#   any string following the prefix in the request
# - regex: use any regular expression
#   allowed by RedirectMatch
#
# YAML objects can have these fields:
#
# - from: the URL string or regex to match; required;
#   should begin with a slash "/" except for some regexs
# - to: the URL string or regex to redirect to; required
# - type: optional, defaults to "full";
#   can be "full", "prefix", or "regex"
# - status: HTTP status for redirect;
#   optional, defaults to "temporary";
#   can be "permanent" (301) or "temporary" (302);
#   (Apache uses "temp" for "temporary")
#
# For the "full" and "prefix" types,
# the URL strings are rewritten as escaped regular expressions,
# with "^" and "$" anchors.
# Any regular expression special characters (e.g. ., *, ?, [])
# will be escaped: they will not match as regular expressions.
#
# For the "prefix" type, "(.*)" is also appended to the "from" field
# and "$1" is appended to the "to" field,
# to configure the prefix match.
#
# For the "regex" type, the "from" and "to" fields
# are assumed to be valid regular expressions,
# and are not checked or modified.
#
# Only use "regex" if "full" or "prefix" are insufficient.
#
# The order of YAML objects will be the order
# of the Apache directives.

import sys, yaml, re, urllib.parse

def clean_from(s):
  """Given a URL string,
  return an escaped regular expression for matching that string.
  Only forward-slashes are not escaped."""
  r = s.strip()
  r = urllib.parse.urlparse(r).geturl()
  r = re.escape(r)
  r = r.replace('\\/', '/')
  return r

def clean_to(s):
  """Given a URL string,
  return an escaped regular expression for matching that string."""
  return urllib.parse.urlparse(s.strip()).geturl()

entries = yaml.load(sys.stdin)

i = 0
for entry in entries:
  i += 1

  # Validate "from" field
  if not 'from' in entry \
      or entry['from'] is None \
      or entry['from'].strip() == '':
    raise ValueError('Missing "from" field for entry %d' % i)

  # Validate "to" field
  if not 'to' in entry \
      or entry['to'] is None \
      or entry['to'].strip() == '':
    raise ValueError('Missing "to" field for entry %d' % i)

  # Validate status code
  if not 'status' in entry:
    entry['status'] = 'temporary'
  if entry['status'] == 'temporary':
    entry['status_type'] = 'temp'
  elif entry['status'] == 'permanent':
    entry['status_type'] = 'permanent'
  else:
    raise ValueError('Invalid status "%s" for entry %d' % (entry['status'], i))

  # Validate "type" field and build regular expression
  if not 'type' in entry:
    entry['type'] = 'full'
  if entry['type'] == 'full':
    entry['from_re'] = '^%s$' % clean_from(entry['from'])
    entry['to_re']   = clean_to(entry['to'])
  elif entry['type'] == 'prefix':
    entry['from_re'] = '^%s(.*)$' % clean_from(entry['from'])
    entry['to_re']   = clean_to(entry['to']) + '$1'
    pass
  elif entry['type'] == 'regex':
    entry['from_re'] = entry['from']
    entry['to_re']   = entry['to']
  else:
    raise ValueError('Invalid "%s" for entry %d' % (entry['type'], i))

  print('RedirectMatch %s "%s" "%s"' %
      (entry['status_type'], entry['from_re'], entry['to_re']))

