# obo-purls

This repository presents an alternative way to manage OBO Foundry PURLs. Like <https://github.com/perma-id/w3id.org> we use per-directory Apache configuration files (`.htaccess` files), each of which uses `RedirectMatch` directives to redirect PURL requests to their proper targets. Unlike w3id.org, we do not edit the Apache configuration files by hand. Instead we have a simple YAML configuration format, and scripts to translate the YAML configuration into Apache configuration. The YAML files are easier to read and write, and allow us to validate and test PURLs automatically.


## Examples

The following examples are *NOT permanent URLs* -- they are running on a little server that might disappear at any time. But they show how things work:

- http://url.ontodev.org/obo/OBI_0000070 (and other OBI term IDs) redirect to Ontobee pages: http://www.ontobee.org/browser/rdf.php?o=OBI&iri=http://purl.obolibrary.org/obo/OBI_0000070
- http://url.ontodev.org/obo/obi/2014-08-18/obi_core.owl redirects to a specific version of the OBI Core OWL file on SourceForge: http://svn.code.sf.net/p/obi/code/releases/2014-08-18/obi_core.owl
- http://url.ontodev.org/obo/obi/wiki redirects to the OBI wiki: http://obi-ontology.org


## Adding and Updating PURLs

TODO: Explain the update process from the perspective of an ontology developer using this system.



## Configuration Format

Each OBO project using this service gets a [YAML](http://yaml.org) configuration file in `config/`. That YAML configuration file is used to generate an Apache `.htaccess` file for that ontology. That Apache configuration will apply to all PURLs for that project.

For example, PURLs for the OBI project are configured in [`config/obi.yml`](config/obi.yml), which is translated to [`obo/obi/.htaccess`](obo/obi/.htaccess), and which controls all PURLs that begin with `http://purl.obolibrary.org/obo/obi/`.

The `.htaccess` file should not be edited! Changes should only be made in the YAML configuration file.

Each YAML configuration file contains the keyword `entries:` followed by a list of entries. Each entry defines an Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch) directive for matching URLs and redirecting to new URLs. Every entry begins with a `- `, followed by keywords and values on indented lines. There are three types of entries:

1. **exact**: The simplest entry matches an exact URL and returns an exact replacement
2. **prefix**: These entries match the first part of a URL and replace just that prefix part
3. **regex**: These entries use powerful regular expressions, and should be avoided unless absolutely necessary.

The `#` character indicates a comment, which is not considered part of the configuration.

See the [`tools/examples/test2.yml`](tools/examples/test2.yml) and [`tools/examples/test2.htaccess`](tools/examples/test2.htaccess) for examples.


### Exact

In the most common case, your PURL should match a unique URL and redirect to a unique URL. Here's an example from the `config/obi.yml` file:

    - exact: /obi.owl
      replacement: http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl

This entry will match exactly the URL `http://purl.obolibrary.org/obo/obi/obi.owl`, and it will redirect to exactly `http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl`. The matched domain name is fixed `http://purl.obolibrary.org`; the next part is project-specific `/obo/obi/`; the final part is taken from the entry `/obi.owl`. The replacement is expected to be a valid, absolute URL, starting with `http`.

Behind the scenes, the entry is translated into an Apache RedirectMatch directive in `obo/obi/.htaccess` by escaping special characters and "anchoring" with initial `^`, the project's base URL, and final `$`:

    RedirectMatch temp "^/2015\-09\-15/obi\.owl$" "http://svn.code.sf.net/p/obi/code/releases/2015-09-15/obi.owl"


### Prefix

You can also match and replace just the first part of a URL, leaving the rest unchanged. This allows you to define one entry that redirects many URLs matching a common prefix. Another example from `config/obi.yml`:

    - prefix: /branches/
      replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/

This entry will match the URL `http://purl.obolibrary.org/obo/obi/branches/obi.owl` (for example), replace the first part `http://purl.obolibrary.org/obo/obi/branches/` with `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/`, resulting in `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/obi.owl`. Effectively, the `obi.owl` is appended to the replacement.

The translation is similar, with the addition of `(.*)` wildcard and a `$1` "backreference" at the ends of the given strings:

    RedirectMatch temp "^/branches/(.*)$" "http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/$1"


### Regex

Regular expression entries should only be needed very rarely, and should always be used very carefully.

For the regular expression type, the value of the `regex:` and `replacement:` keywords should contain regular expressions in exactly the format expected by Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch). The values will be quoted, but no other changes will be made to them.


### Temporary and Permanent

Any entry can have a `status:` keyword. By default, every entry uses "temporary" (HTTP 302) status. If you *really* know what you're doing, you can set the status to "permanent" (HTTP 301).


### Order of Entries

Apache RedirectMatch directives are processed in the [order that they appear](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#order) in the configuration file. Be careful that your `prefix` and `regex` entries do not conflict with your other entries. The YAML-to-Apache translation preserves the order of entries, so you can control the order of processing, but it's best to avoid conflicts.


## Migrating Configuration

OBO projects currently use OCLC for managing PURLs. This project aims to replace OCLC in a straightforward way.

The `Makefile` contains some code for fetching the PURL records for a given ontology ID from OCLC in XML format, and converting the XML to YAML. This should be a one-time migration. Going forward, the YAML configuration should be edited directly.

The order of the migrated entries is: `exact` first (*should* be in the order they were created), followed by `prefix` entries from longest `prefix` to shortest. This order avoids nasty conflicts and has been tested to preserve the OCLC behaviour.

You can run migration for a single ontology at a time, by its ID (usually lower case):

    make migrate-obi

The tool will refuse to overwrite existing YAML configuration files. If you are running a test server (see next section) you can test the configuration as you are migrating:

    make migrate-obi && make all test


## Development and Testing

Developers can test their changes using a local virtual machine. First install [VirtualBox](https://www.virtualbox.org) and [Vagrant](https://www.vagrantup.com). Then check out a copy of this repository and start a virtual machine like so:

    git clone https://github.com/jamesaoverton/obo-purls.git
    cd obo-purls/tools
    vagrant up

This will download a Debian Linux virtual machine, start it, and configure it as a web server. The `/var/www/obo-purls` directory of the VM is synced with your local `obo-purls` directory. You can then log in and rebuild the `.htaccess` files:

    vagrant ssh
    cd /var/www/obo-purls
    make

Test your changes in your browser using URLs starting with `http://172.16.100.10/obo/`, such as [`http://172.16.100.10/obo/OBI_0000070`](http://172.16.100.10/obo/OBI_0000070). You can also run an automated test of all the configured URLs like so:

    make all test

Test results will be listed in `tests/development/*.tsv` with their expected and actual values. If you are making changes to the project tools, you can test them against the `tools/examples/` files with:

    make clean test-examples

When you are done with the VM, log out with `exit`. Then you can choose to suspend the VM with

    vagrant suspend

or delete the VM with

    vagrant destroy

You can test against the production PURL server using `make test-production`. We only make one request per second, to avoid abusing the server, so this can take along time.


## Deployment

Deployment is automated using [Ansible](http://ansible.com), and targets a stock Debian 8 Linux server. You should install on a **fresh** server, not one that's running other applications, unless you **really** know what you're doing.

Install Ansible on your local machine, add the IP address or hostname of your target server to `tools/hosts`, then run:

    cd tools
    ansible-playbook -i hosts site.yml

Ansible uses SSH to connect to the server an execute the tasks in [`tools/site.yml`](tools/site.yml). If you have trouble connecting, you may have to adjust your SSH configuration to be more automatic, say by editing your `.ssh/config`.

You can re-run Ansible as you make changes. Once the system is running, it will fetch changes from the master Git repository every 10 minutes. You can use the `tools/test.py` script to check your work, e.g.:

    tools/test.py url.ontodev.org config/obi.yml

