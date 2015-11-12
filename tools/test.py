#!/usr/bin/env python3
#
# Read a YAML configuration file,
# make a series of HTTP HEAD requests to a target server,
# and report the results in a table.

import argparse, sys, yaml, http.client, time


# Parse command line arguments,
# read the YAML file and collect tests,
# run tests using HTTP HEAD requests,
# and write results to the report file.
def main():
  parser = argparse.ArgumentParser(description='Translate YAML to .htaccess')
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
      type=argparse.FileType('w'),
      default=sys.stdout,
      nargs='?',
      help='write to the TSV file (or STDOUT)')
  args = parser.parse_args()

  # Load YAML document and look for 'entries' list.
  document = yaml.load(args.yaml_file)

  if not 'base_url' in document \
      or type(document['base_url']) is not str:
    raise ValueError('YAML document must contain "base_url" string')
  base_url = document['base_url']

  if not 'entries' in document \
      or type(document['entries']) is not list:
    raise ValueError('YAML document must contain "entries" list')

  # Collect the tests to run.
  tests = []
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
    sys.stdout.flush()
    time.sleep(args.delay)


def process_entry(base_url, i, entry):
  """Given a base URL, an index, and an entry dictionary,
  return a list of tests to run."""
  tests = []
  test = {}

  # Check entry data type.
  if type(entry) is not dict:
    raise ValueError('Entry %d is invalid: "%s"' % (i, entry))

  # Validate "replacement" field
  if not 'replacement' in entry \
      or entry['replacement'] is None \
      or entry['replacement'].strip() == '':
    raise ValueError('Missing "replacement" field for entry %d' % i)

  # Validate status code.
  status = '302'
  if 'status' in entry:
    if entry['status'] == 'temporary':
      status = '302'
    elif entry['status'] == 'permanent':
      status = '302'
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
        print(test)
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

  expected = [test['status'], test['replacement']]
  actual = [str(response.status), location]
  result = 'FAIL'
  if actual == expected:
    result = 'PASS'

  return [result, test['source']] + expected + actual


if __name__ == "__main__":
    main()
