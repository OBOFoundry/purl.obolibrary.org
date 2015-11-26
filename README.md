# OBO PURLs

[![Build Status](https://travis-ci.org/OBOFoundry/purl.obolibrary.org.svg)](https://travis-ci.org/OBOFoundry/purl.obolibrary.org)

The OBO community is transitioning away from [PURL.org](http://purl.org) for managing Persistent URLs.

This repository provides a new way to manage OBO Foundry PURLs. Like <https://github.com/perma-id/w3id.org> we use per-directory Apache configuration files (`.htaccess` files), each of which uses `RedirectMatch` directives to redirect PURL requests to their proper targets. Unlike w3id.org, we do not edit the Apache configuration files by hand. Instead we have a simple YAML configuration format, and scripts to translate the YAML configuration into Apache configuration. The YAML files are easier to read and write, and allow us to validate and test PURLs automatically.


## Transition

The new system is not yet handling http://purl.obolibrary.org/obo/ PURLs, but is available for testing: see the next section.

During the transition period, both the new system and the old system will be used:

1. The new system will try to match and handle every request. This allows us to update our PURLs and add new ones using the new system.
2. If the new system cannot match a request, it will redirect to the old system, and the old system will handle the request. This provides a safety net.

The new system will log requests that it cannot match. We will review these logs and update the new system as required.


## Examples

The following examples are **NOT permanent URLs** -- they are running on a test server that will soon be shut down. But they show how things work:

- http://url.ontodev.org/obo/OBI_0000070 (and other OBI term IDs) redirect to Ontobee pages: http://www.ontobee.org/browser/rdf.php?o=OBI&iri=http://purl.obolibrary.org/obo/OBI_0000070
- http://url.ontodev.org/obo/obi/2014-08-18/obi_core.owl redirects to a specific version of the OBI Core OWL file on SourceForge: http://svn.code.sf.net/p/obi/code/releases/2014-08-18/obi_core.owl
- http://url.ontodev.org/obo/obi/wiki redirects to the OBI wiki: http://obi-ontology.org


## Adding and Updating PURLs

Please use one of these four options to make changes to the PURLs:

1. [Create a new issue](https://github.com/OBOFoundry/purl.obolibrary.org/issues/new) describing the change you require.

2. [Browse to the configuration file you want to change](https://github.com/OBOFoundry/purl.obolibrary.org/tree/master/config) and click the "pencil" icon to edit it.

3. [Add a new configuration file](https://github.com/OBOFoundry/purl.obolibrary.org/new/master/config).

4. [Fork this repository](https://help.github.com/articles/fork-a-repo/) and [make a pull request](https://help.github.com/articles/using-pull-requests/).


## Configuration Format

Each OBO project using this service gets a [YAML](http://yaml.org) configuration file in `config/`. That YAML configuration file is used to generate an Apache `.htaccess` file for that ontology. That Apache configuration will apply to all PURLs for that project.

The name of of the YAML configuration file must the project's [IDSPACE](http://obofoundry.org/id-policy.html). This is case sensitive, and usually uppercase.

The YAML file must contain a `purl_rules:` list of rules, described below. Here's an example adapted from the [`config/OBI.yml`](config/OBI.yml) file:

    purl_rules:
    - term_browser: ontobee
      tests:
      - path: /obo/OBI_0000070
        replacement: http://www.ontobee.org/browser/rdf.php?o=OBI&iri=http://purl.obolibrary.org/obo/OBI_0000070

    - path: /obo/obi.owl
      replacement: http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl

    - path: /obo/obi.obo
      replacement: http://www.berkeleybop.org/ontologies/obi.obo

    - path: /obo/obi/wiki
      replacement: http://obi-ontology.org

    - prefix: /obo/obi/wiki/
      replacement: http://obi-ontology.org/page/


### PURL Rules

Each YAML configuration file contains the keyword `purl_rules:` followed by a list of rules. Each rule defines an Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch) directive for matching URLs and redirecting to new URLs. Every rule begins with a `- `, followed by keywords and values on indented lines. There are three types of rules:

1. **path**: The simplest rule matches an exact URL and returns an exact replacement
2. **prefix**: These rules match the first part of a URL and replace just that prefix part
3. **regex**: These rules use powerful regular expressions, and should be avoided unless absolutely necessary.
4. **term_browser**: Special rules for term browsers such as [Ontobee](http://www.ontobee.org)

The `#` character indicates a comment, which is not considered part of the configuration.

See the [`tools/examples/Test2.yml`](tools/examples/Test2.yml) file for more examples.


#### Path

In the most common case, your PURL should match a unique URL and redirect to a unique URL. Here's an example from the `config/OBI.yml` file:

    - path: /obo/obi.owl
      replacement: http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl

This rule will match exactly the URL `http://purl.obolibrary.org/obo/obi.owl`, and it will redirect to exactly `http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl`. The matched domain name is fixed `http://purl.obolibrary.org`; the final part is taken from the rule `/obo/obi.owl`. The replacement is expected to be a valid, absolute URL, starting with `http`.

Behind the scenes, the rule is translated into a case insensitive Apache RedirectMatch directive in `obo/.htaccess` by escaping special characters and "anchoring" with initial `^`, the project's base URL, and final `$`:

    RedirectMatch temp "(?i)^/obo/obi\.owl$" "http://svn.code.sf.net/p/obi/code/releases/2015-09-15/obi.owl"


#### Prefix

You can also match and replace just the first part of a URL, leaving the rest unchanged. This allows you to define one rule that redirects many URLs matching a common prefix. Another example from `config/OBI.yml`:

    - prefix: /obo/obi/branches/
      replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/

This rule will match the URL `http://purl.obolibrary.org/obo/obi/branches/obi.owl` (for example), replace the first part `http://purl.obolibrary.org/obo/obi/branches/` with `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/`, resulting in `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/obi.owl`. Effectively, the `obi.owl` is appended to the replacement.

The translation is similar, with the addition of `(.*)` wildcard and a `$1` "backreference" at the ends of the given strings:

    RedirectMatch temp "(?i)^/obo/obi/branches/(.*)$" "http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/$1"


#### Regex

Regular expression rules should only be needed very rarely, and should always be used very carefully.

For the regular expression type, the value of the `regex:` and `replacement:` keywords should contain regular expressions in exactly the format expected by Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch). The values will be quoted, but no other changes will be made to them. Consider using `(?i)` to make the match case insensitive.


#### Term Browser

A `term_browser: ontobee` rule is a shortcut to redirect your ontology terms to Ontobee. It generates a directive like:

    RedirectMatch seeother "(?i)^/obo/OBI_(\d+)$" "http://www.ontobee.org/browser/rdf.php?o=OBI&iri=http://purl.obolibrary.org/obo/OBI_$1"


#### Tests

Every `prefix`, `regex`, and `term_browser` rule should also have a `tests:` keyword, with a list of additional URLs to check. Each test requires a `path:` and a `replacement:` value. Here's an example:

    - prefix: /obo/obi/branches/
      replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/
      tests:
      - path: /obo/obi/branches/obi.owl
        replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/obi.owl


#### Order of Rules

Apache RedirectMatch directives are processed in the [order that they appear](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#order) in the configuration file. Be careful that your `prefix` and `regex` rules do not conflict with your other rules. The YAML-to-Apache translation preserves the order of rules, so you can control the order of processing, but it's best to avoid conflicts.


## Custom Term Browsers

If your project does not use Ontobee as a term browser, you should provide a `regex` rule. Here's an example for [ChEBI](https://www.ebi.ac.uk/chebi/):

    - regex: ^/obo/CHEBI_(\d+)$
      replacement: http://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:$1
      status: see other
      level: top
      tests:
      - path: /obo/CHEBI_15377
        replacement: http://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377

Note that term redirect rules are case sensitive.

Since these are `regex` rules, and could affect multiple projects, we prefer that OBO admins are the only ones to edit them. If you need a change to the term redirect rule for your project, please [create a new issue](https://github.com/OBOFoundry/purl.obolibrary.org/issues/new).


## Migrating Configuration

OBO projects currently use OCLC for managing PURLs. This project aims to replace OCLC in a straightforward way.

The `Makefile` contains some code for fetching the PURL records for a given ontology ID from OCLC in XML format, and converting the XML to YAML. This should be a one-time migration, and it requires some manual editing and checking. Going forward, the YAML configuration should be edited directly.

The order of the migrated rules is: `path` first (*should* be in the order they were created), followed by `prefix` rules from longest `prefix` to shortest. This order avoids nasty conflicts and has been tested to preserve the OCLC behaviour.

You can run migration for a single ontology at a time, by its ID (usually lower case):

    make migrate-OBI

The tool will refuse to overwrite existing YAML configuration files. If you are running a test server (see next section) you can test the configuration as you are migrating:

    make migrate-OBI && make all test


## Development and Testing

Developers can test their changes using a local virtual machine. First install [VirtualBox](https://www.virtualbox.org) and [Vagrant](https://www.vagrantup.com). Then check out a copy of this repository and start a virtual machine like so:

    git clone https://github.com/OBOFoundry/purl.obolibrary.org.git
    cd purl.obolibrary.org/tools
    vagrant up

This will download a Ubuntu Linux virtual machine, start it, and configure it as a web server. The `/var/www/purl.obolibrary.org` directory of the VM is synced with your local `purl.obolibrary.org` directory. You can then log in and rebuild the `.htaccess` files:

    vagrant ssh
    cd /var/www/purl.obolibrary.org
    make

Test your changes in your browser using URLs starting with `http://172.16.100.10/obo/`, such as [`http://172.16.100.10/obo/OBI_0000070`](http://172.16.100.10/obo/OBI_0000070). You can also run an automated test of all the configured URLs like so:

    make all test

Test results will be listed in `tests/development/*.tsv` with their expected and actual values. If you are making changes to the project tools, you can test them against the `tools/examples/` files with:

    make clean test-tools

When you are done with the VM, log out with `exit`. Then you can choose to suspend the VM with

    vagrant suspend

or delete the VM with

    vagrant destroy

You can test against the production PURL server using `make test-production`. We only make one request per second, to avoid abusing the server, so this can take along time.


## Deployment

Deployment is automated using [Ansible](http://ansible.com), and targets a stock Ubuntu Linux server. You should install on a **fresh** server, not one that's running other applications, unless you **really** know what you're doing.

Install Ansible on your local machine, add the IP address or hostname of your target server to `tools/hosts`, then run:

    cd tools
    ansible-playbook -i hosts site.yml

Ansible uses SSH to connect to the server an execute the tasks in [`tools/site.yml`](tools/site.yml). If you have trouble connecting, you may have to adjust your SSH configuration to be more automatic, say by editing your `.ssh/config`.

You can re-run Ansible as you make changes. Once the system is running, it will fetch changes from the master Git repository every 10 minutes. From your local machine, you can test all URLs against any target server, e.g.:

    export PRODUCTION=url.ontodev.org; make clean test-production

The `make safe-update` task will check [Travis-CI](https://travis-ci.org/OBOFoundry/purl.obolibrary.org) to ensure that the latest build on the master branch passed all automated tests, and that it is newer than the last time `safe-update` completed. Then it will pull from the Git repository and rebuild the site. This *should* be safe for a `cron` task to synchronize PURLs with the repository.
