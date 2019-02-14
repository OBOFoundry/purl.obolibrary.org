#!/usr/bin/env python3

import difflib
import requests
import subprocess
import sys

api_url = 'https://api.travis-ci.org'
repo_slug = 'OBOFoundry/purl.obolibrary.org'
accept_header = {'Accept': 'application/vnd.travis-ci.2.1+json'}

# Get the last build ID from Travis:
resp = requests.get('{}/repos/{}'.format(api_url, repo_slug), headers=accept_header)
if resp.status_code != requests.codes.ok:
  resp.raise_for_status()
last_build_id = resp.json()['repo']['last_build_id']

# Now get the build details:
resp = requests.get('{}/repos/{}/builds/{}'.format(api_url, repo_slug, last_build_id),
                    headers=accept_header)
if resp.status_code != requests.codes.ok:
  resp.raise_for_status()
content = resp.json()

# If the last build did not pass, then do nothing and exit.
if content['build']['state'] != 'passed':
  print("Last build is not green. Not updating.", file=sys.stderr)
  sys.exit(0)

# Otherwise see if the build description is different from the current build
print("Last build is green. Checking whether it is new ...")
build_desc = "#{} {}:    {} {}".format(content['build']['number'], content['build']['state'],
                                       content['commit']['branch'], content['commit']['message'])
# We only want to keep the first line of the last build's description for comparison purposes:
newbuild_lines = build_desc.splitlines(keepends=True)[:1]
with open('.current_build') as infile:
  currbuild_lines = infile.readlines()

diff = list(difflib.unified_diff(currbuild_lines, newbuild_lines))
if not diff:
  print("Last build is not new. Not updating.")
  sys.exit(0)

# Output a diff for information purposes and then do a `git pull` and `make` from the current
# working directory:
for d in diff:
  print(d, end='')
print('\nNew green build available. Updating local repository ...')

subprocess.call(["git", "pull"])
subprocess.call(["make"])
with open('.current_build', 'w') as outfile:
  outfile.write(newbuild_lines.pop())
