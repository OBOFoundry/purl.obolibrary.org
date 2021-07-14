#!/usr/bin/env python3

# Check Github CI build status for the `master` branch of OBOFoundry/purl.obolibrary.org
# If `master` is green (i.e. all tests are passing),
# and the build number is greater than the current build
# (i.e. the last time we updated),
# then pull `master`, run Make, and update .current_build.

import requests
import subprocess
import sys
import os
from types import SimpleNamespace


def printf(fmt, *varargs):
    sys.stdout.write(fmt % varargs)


def git_exec(repo, args):
    git_dir = os.path.join(repo, '.git')
    command = ['git', '--work-tree=' + repo, '--git-dir=' + git_dir] + args.split()

    with open(os.devnull, 'w') as devnull:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=devnull)
        code = result.returncode

        if code != 0:
            raise Exception('failed:{}, code='.format(subprocess.list2cmdline(command), code))

        return result.stdout.decode('utf-8').strip()


def get_repo_slug(repo):
    url = git_exec(repo, 'config --get remote.origin.url')
    pattern = 'github.com/'
    return url[url.index(pattern) + len(pattern):url.rindex('.git')]


if len(sys.argv) > 1:
    repo_dir = sys.argv[1]
else:
    repo_dir = os.getcwd()

repo_slug = get_repo_slug(repo_dir)
printf('repo_slug=%s\n', repo_slug)

branch = git_exec(repo_dir, 'name-rev --name-only HEAD')
printf('branch=%s\n', branch)

head_sha = git_exec(repo_dir, 'rev-parse {}'.format(branch))
printf('head_sha=%s\n', head_sha)

ret = git_exec(repo_dir, 'ls-remote https://github.com/{}.git {}'.format(repo_slug, branch)).split()

if not ret:
    printf('Not a remote branch  %s\n', branch)
    sys.exit(1)

remote_head_sha = ret[0]
printf('remote_head_sha=%s\n', remote_head_sha)

if remote_head_sha == head_sha:
    printf('Nothing has been checked in into %s\n', branch)
    sys.exit(1)

api_url = 'https://api.github.com'
accept_header = {'Accept': 'application/vnd.github.v3+json'}
resp = requests.get('{}/repos/{}/actions/runs'.format(api_url, repo_slug), headers=accept_header)

if resp.status_code != requests.codes.ok:
    resp.raise_for_status()

json_result = SimpleNamespace(**resp.json())
workflow_runs = map(lambda x: SimpleNamespace(**x), json_result.workflow_runs)
workflow_run = next(filter(lambda x: x.head_sha == remote_head_sha, workflow_runs), None)

if not workflow_run:
    printf('Workflow run not found for %s\n', remote_head_sha)
    sys.exit(1)

assert workflow_run.head_branch == branch, 'branch check failed'
assert workflow_run.event == 'push', 'event check failed'

if workflow_run.status != 'completed' or workflow_run.conclusion != 'success':
    printf('workflow run failed checks: status=%s conclusion=%s\n',
           workflow_run.status, workflow_run.conclusion)
    sys.exit(1)

printf("workflow: id=%d, run_number=%d\n", workflow_run.id, workflow_run.run_number)

git_exec(repo_dir, 'fetch origin')
git_exec(repo_dir, 'merge ' + remote_head_sha)
head_sha = git_exec(repo_dir, 'rev-parse {}'.format(branch)).split()[0]
printf('head_sha_after_git_merge=%s\n', head_sha)

if remote_head_sha != head_sha:
    printf('Something went terribly wrong when merging latest hash  %s\n', branch)
    sys.exit(1)

if subprocess.call(["make"]) != 0:
    printf('make failed on %s\n', branch)
    sys.exit(1)

printf('updated successfully on %s\n', branch)
sys.exit(0)
