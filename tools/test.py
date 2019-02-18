#!/usr/bin/env python3
#
# Read a YAML configuration file,
# make a series of HTTP HEAD requests to a target server,
# and report the results in a table.
#
# NOTE: Currently only tests `example_terms` when `term_browser: ontobee`.

import argparse
import http.client
import os
import sys
import time
import yaml
from urllib.parse import unquote


# Parse command line arguments,
# read the YAML file and collect tests,
# run tests using HTTP HEAD requests,
# and write results to the report file.
def main():
  parser = argparse.ArgumentParser(description='Test a YAML configuration by making HTTP requests')
  parser.add_argument('-d', '--delay', metavar='D',
                      type=float,
                      default=1,
                      help='delay between requests in seconds (default 1)')
  parser.add_argument('-t', '--timeout', metavar='T',
                      type=float,
                      default=10,
                      help='connection timeout in seconds (default 10)')
  parser.add_argument('domain',
                      type=str,
                      default='172.16.100.10',
                      nargs='?',
                      help='target server (default 172.16.100.10)')
  parser.add_argument('yaml_file',
                      type=argparse.FileType('r'),
                      default=sys.stdin,
                      nargs='?',
                      help='read from the YAML file (or STDIN)')
  parser.add_argument('report_file',
                      type=str,
                      nargs='?',
                      help='write to the TSV file (or STDOUT)')
  args = parser.parse_args()

  # Create the report file if has been specified, otherwise set it to sys.stdout:
  if args.report_file is not None:
    try:
      args.report_file = open(args.report_file, 'w')
    except FileNotFoundError:
      os.makedirs(os.path.dirname(args.report_file))
      args.report_file = open(args.report_file, 'w')
  else:
    args.report_file = sys.stdout

  # Load YAML document and look for 'entries' list.
  document = yaml.load(args.yaml_file)

  if 'idspace' not in document \
     or type(document['idspace']) is not str:
    raise ValueError('YAML document must contain "idspace" string')
  idspace = document['idspace']

  if 'base_url' not in document \
     or type(document['base_url']) is not str:
    raise ValueError('YAML document must contain "base_url" string')
  base_url = document['base_url']

  tests = []

  # Collect the tests to run.
  if 'base_redirect' in document:
    tests += [{
      'source': base_url,
      'replacement': document['base_redirect'],
      'status': '302'
    }]

  if 'products' in document \
     and type(document['products']) is list:
    i = 0
    for product in document['products']:
      i += 1
      tests += process_product(i, product)

  if 'term_browser' in document \
     and document['term_browser'].strip().lower() == 'ontobee' \
     and 'example_terms' in document \
     and type(document['example_terms']) is list:
    i = 0
    for example_term in document['example_terms']:
      i += 1
      tests += process_ontobee(idspace, i, example_term)

  if 'tests' in document:
    i = 0
    status = '302'
    for test_entry in document['tests']:
      i += 1
      test = {'status': status}
      if 'from' in test_entry:
        test['source'] = base_url + test_entry['from']
      if 'to' in test_entry:
        test['replacement'] = test_entry['to']
      if 'source' in test and 'replacement' in test:
        tests.append(test)
      else:
        raise ValueError('Invalid test %d in global tests' % i)

  if 'entries' in document \
     and type(document['entries']) is list:
    i = 0
    for entry in document['entries']:
      i += 1
      tests += process_entry(base_url, i, entry)

  # Write report table header.
  args.report_file.write('\t'.join([
    'Result', 'Source URL',
    'Expected Status', 'Expected URL',
    'Actual Status', 'Actual URL'
  ]) + '\n')

  # Run the tests and add results to the report table.
  conn = http.client.HTTPConnection(args.domain, timeout=args.timeout)
  for test in tests:
    results = run_test(conn, test)
    args.report_file.write('\t'.join(results) + '\n')
    args.report_file.flush()
    time.sleep(args.delay)

  args.report_file.close()


def process_product(i, product):
  """Given an index, and a product dictionary,
  return a list with a test to run."""
  for key in product:
    return [{
      'source': '/obo/' + key,
      'replacement': product[key],
      'status': '302'
    }]


ontobee = 'http://www.ontobee.org/browser/rdf.php?o=%s&iri=http://purl.obolibrary.org/obo/'


def process_ontobee(idspace, i, example_term):
  """Given an ontology IDSPACE, an index, and an example term ID,
  return a list with a test to run."""
  return [{
    'source': '/obo/' + example_term,
    'replacement': (ontobee % idspace) + example_term,
    # 'replacement': 'http://ontologies.berkeleybop.org/' + example_term,
    'status': '303'
  }]


def process_entry(base_url, i, entry):
  """Given a base URL, an index, and an entry dictionary,
  return a list of tests to run."""
  tests = []
  test = {}

  # Check entry data type.
  if type(entry) is not dict:
    raise ValueError('Entry %d is invalid: "%s"' % (i, entry))

  # Validate "replacement" field
  if 'replacement' not in entry \
     or entry['replacement'] is None \
     or entry['replacement'].strip() == '':
    raise ValueError('Missing "replacement" field for entry %d' % i)

  # Validate status code.
  status = '302'
  if 'status' in entry:
    if entry['status'] == 'permanent':
      status = '301'
    elif entry['status'] == 'temporary':
      status = '302'
    elif entry['status'] == 'see other':
      status = '303'
    else:
      raise ValueError('Invalid status "%s" for entry %d' % (entry['status'], i))
  test['status'] = status

  # Determine the type for this entry.
  types = []
  if 'exact' in entry:
    test['source'] = base_url + entry['exact']
    test['replacement'] = entry['replacement']
    tests.append(test)
  elif 'prefix' in entry:
    test['source'] = base_url + entry['prefix']
    test['replacement'] = entry['replacement']
    tests.append(test)

  # If there is a 'tests' list, collect those tests as well.
  # They all have the same status code as their parent.
  if 'tests' in entry:
    t = 0
    for test_entry in entry['tests']:
      t += 1
      test = {'status': status}
      if 'from' in test_entry:
        test['source'] = base_url + test_entry['from']
      if 'to' in test_entry:
        test['replacement'] = test_entry['to']
      if 'source' in test and 'replacement' in test:
        tests.append(test)
      else:
        raise ValueError('Invalid test %d for entry %d' % (t, i))

  return tests


def run_test(conn, test):
  """Given an connection and a test dictionary,
  make a HTTP HEAD request,
  compare the actual result to the expected result,
  and return a list of result entries."""

  conn.request("HEAD", test['source'])
  response = conn.getresponse()
  response.read()

  location = response.getheader('Location')
  if location is None:
    location = ''
  else:
    location.replace('&amp;', '&')

  expected = [test['status'], unquote(test['replacement'])]
  actual = [str(response.status), unquote(location)]
  result = 'FAIL'
  if actual == expected:
    result = 'PASS'

  return [result, test['source']] + expected + actual


if __name__ == "__main__":
    main()
