#!/usr/bin/env python3

import sys, yaml, http.client, time

# Load YAML document and look for 'entries' list.
document = yaml.load(sys.stdin)

if not 'entries' in document \
    or document['entries'] is None \
    or type(document['entries']) is not list:
  raise ValueError('Document must contain "entries" list')

domain = sys.argv[1]
base   = sys.argv[2]
delay  = float(sys.argv[3])
conn = http.client.HTTPConnection(domain, timeout=10)

print('\t'.join([
  'Result', 'Source URL',
  'Expected Status', 'Expected URL',
  'Actual Status', 'Actual URL'
]))

tests = []

# For each entry,
i = 0
for entry in document['entries']:
  i += 1
  test = {}

  # Check entry data type
  if type(entry) is not dict:
    raise ValueError('Entry %d is invalid: "%s"' % (i, entry))

  # Validate "replacement" field
  if not 'replacement' in entry \
      or entry['replacement'] is None \
      or entry['replacement'].strip() == '':
    raise ValueError('Missing "replacement" field for entry %d' % i)

  # Validate status code
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
    test['source'] = base + entry['exact']
    test['replacement'] = entry['replacement']
    tests.append(test)
  elif 'prefix' in entry:
    test['source'] = base + entry['prefix']
    test['replacement'] = entry['replacement']
    tests.append(test)

  if 'tests' in entry:
    t = 0
    for test_entry in entry['tests']:
      t += 1
      test = {'status': status}
      if 'from' in test_entry:
        test['source'] = base + test_entry['from']
      if 'to' in test_entry:
        test['replacement'] = test_entry['to']
      if 'source' in test and 'replacement' in test:
        tests.append(test)
      else:
        print(test)
        raise ValueError('Invalid test %d for entry %d' % (t, i))


for test in tests:
  expected = [test['status'], test['replacement']]

  conn.request("HEAD", test['source'])
  response = conn.getresponse()

  location = response.getheader('Location')
  if location is None:
    location = ''
  else:
    location.replace('&amp;', '&')

  actual = [str(response.status), location]
  response.read()

  result = 'FAIL'
  if actual == expected:
    result = 'PASS'

  print('\t'.join([result, test['source']] + expected + actual))
  sys.stdout.flush()
  time.sleep(delay)

