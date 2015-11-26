#!/usr/bin/env python3
#
# Read a YAML configuration file,
# make a series of HTTP HEAD requests to a target server,
# and report the results in a table.
#
# NOTE: Currently only tests `example_terms` when `term_browser: ontobee`.

import argparse, sys, os.path, yaml, http.client, time, urllib.parse


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
      help='read from the YAML file')
  parser.add_argument('report_file',
      type=argparse.FileType('w'),
      default=sys.stdout,
      nargs='?',
      help='write to the TSV file (or STDOUT)')
  args = parser.parse_args()

  yaml_file_base_name = os.path.basename(args.yaml_file.name)
  idspace = os.path.splitext(yaml_file_base_name)[0]

  # Load YAML document and look for 'entries' list.
  document = yaml.load(args.yaml_file)

  tests = []

  if 'purl_rules' in document \
      and type(document['purl_rules']) is list:
    for rule in document['purl_rules']:
      tests += process_rule(rule)

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


def process_rule(rule):
  """Given a rule dictionary,
  return a list of tests to run."""
  tests = []
  test = {}

  # Check rule data type.
  if type(rule) is not dict:
    raise ValueError('Rule %d is invalid:\n%s' % rule)

  # Validate status code.
  status = '302'
  if 'term_browser' in rule:
    status = '303'
  if 'status' in rule:
    if rule['status'] == 'permanent':
      status = '301'
    elif rule['status'] == 'temporary':
      status = '302'
    elif rule['status'] == 'see other':
      status = '303'
    else:
      raise ValueError('Invalid status "%s":\n' % (rule['status'], rule))
  test['status'] = status

  # Determine the type for this rule.
  if 'path' in rule:
    test['source'] = rule['path']
    test['replacement'] = rule['replacement']
    tests.append(test)
  elif 'prefix' in rule:
    test['source'] = rule['prefix']
    test['replacement'] = rule['replacement']
    tests.append(test)

  # If there is a 'tests' list, collect those tests as well.
  # They all have the same status code as their parent.
  if 'tests' in rule:
    t = 0
    for test_rule in rule['tests']:
      t += 1
      test = {'status': status}
      if 'path' in test_rule:
        test['source'] = test_rule['path']
      if 'replacement' in test_rule:
        test['replacement'] = test_rule['replacement']
      if 'source' in test and 'replacement' in test:
        tests.append(test)
      else:
        raise ValueError('Invalid test:\n%s' % test_rule)

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
  if test['replacement'].startswith('/obo/'):
    location = urllib.parse.urlparse(location).path
  location = location.replace('&amp;', '&')

  expected = [test['status'], test['replacement']]
  actual = [str(response.status), location]
  result = 'FAIL'
  if actual == expected:
    result = 'PASS'

  return [result, test['source']] + expected + actual


if __name__ == "__main__":
    main()
