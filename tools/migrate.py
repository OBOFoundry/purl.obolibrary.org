#!/usr/bin/env python3
#
# Use a SAX parser to efficiently read selected fields from XML.

import sys, xml.sax, re

base = sys.argv[1]
exact = []
prefix = []

class OCLCHandler(xml.sax.ContentHandler):
  def __init__(self):
    self.count = 0
    self.content = ''
    self.entry = {}

  # If this is a new entry, clear all variables.
  # Always clear the content buffer.
  def startElement(self, name, attrs):
    self.content = ''
    if name == 'purl':
      self.count += 1
      self.entry = {}

  # Accumulate characters.
  def characters(self, content):
    self.content += content

  # Get the first value found for accession, name, and fullName.
  # If this is the end of an entry, print a row of results.
  def endElement(self, name):
    if name in ('type', 'id', 'url'):
      if self.content.strip() == '':
        raise ValueError('Empty <%s> for <purl> %d' % (name, self.count))
      self.entry[name] = self.content.strip()
    elif name == 'purl':
      if not 'id' in self.entry:
        raise ValueError('No <id> for <purl> %d' % self.count)
      self.entry['id'] = re.sub(r'^' + base, '', self.entry['id'])
      if not 'url' in self.entry:
        raise ValueError('No <url> for <purl> %d' % self.count)
      if not 'type' in self.entry:
        raise ValueError('No <type> for <purl> %d' % self.count)
      elif self.entry['type'] == '302':
        self.entry['rule'] = 'exact'
        exact.append(self.entry)
      elif self.entry['type'] == 'partial':
        self.entry['rule'] = 'prefix'
        prefix.append(self.entry)
      else:
        raise ValueError('Unknown type "%s" for <purl> %d' %
            (self.entry['type'], self.count))

parser = xml.sax.make_parser()
parser.setContentHandler(OCLCHandler())
parser.parse(sys.stdin)

print('# PURL configuration for http://purl.obolibrary.org' + base)
print('')
print('entries:')

entries = exact + sorted(prefix, key=lambda k: len(k['id']), reverse=True)
for entry in entries:
  print('- %s: %s' % (entry['rule'], entry['id']))
  print('  replacement: ' + entry['url'])
  print('')
