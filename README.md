# OBO PURLs

This repository provides tools for managing OBO Foundry Permanent URLs (PURLs). Like <https://github.com/perma-id/w3id.org> we use per-directory Apache configuration files (`.htaccess` files), each of which uses `RedirectMatch` directives to redirect PURL requests to their proper targets. Unlike w3id.org, we do not edit the Apache configuration files by hand. Instead we have a simple YAML configuration format, and scripts to translate the YAML configuration into Apache configuration. The YAML files are easier to read and write, and allow us to validate and test PURLs automatically.


## Status

All http://purl.obolibrary.org/obo/ PURLs are now handled by this system, with the exception of some [open issues](https://github.com/OBOFoundry/purl.obolibrary.org/issues). PURLs that do not match any rule in this system will fall back to the old [PURL.org](http://purl.org) system.


## Adding and Updating PURLs

Please use one of these four options to make changes to the PURLs:

1. [Create a new issue](https://github.com/OBOFoundry/purl.obolibrary.org/issues/new) describing the change you require.

2. [Browse to the configuration file you want to change](https://github.com/OBOFoundry/purl.obolibrary.org/tree/master/config) and click the "pencil" icon to edit it.

3. [Add a new configuration file](https://github.com/OBOFoundry/purl.obolibrary.org/new/master/config).

4. [Fork this repository](https://help.github.com/articles/fork-a-repo/) and [make a pull request](https://help.github.com/articles/using-pull-requests/).

All changes are reviewed before they are merged into the `master` branch. Once merged, updated PURLs will be active within 20 minutes.


## Configuration Format

Each OBO project using this service gets a [YAML](http://yaml.org) configuration file in `config/`. That YAML configuration file is used to generate an Apache `.htaccess` file for that ontology. That Apache configuration will apply to all PURLs for that project.

Every YAML configuration file must have these fields:

- `idspace:` the project's [IDSPACE](http://obofoundry.org/id-policy.html), case sensitive, usually uppercase
- `base_url:` the part of a PURL that comes after the domain, usually lowercase
- `term_browser:` usually [`ontobee`](http://ontobee.org) or [`ols`](https://www.ebi.ac.uk/ols/index) but can be `custom` (see below)
- `products:` a list of primary files for the ontology and the URLs to redirect them to; an `.owl` file is required, and an `.obo` file is optional

Optional fields include:

- `example_terms:` a list of one or more term IDs for automated testing
- `base_redirect:` If your project redirects its `base_url`, then you will need a `base_redirect:` entry. So `base_redirect: http://obi-ontology.org` will redirect <http://purl.obolibrary.org/obo/obi> to <http://obi-ontology.org>.
- `entries:` a list of other PURLs under the `base_url`, see below

Here's an example adapted from the [`config/obi.yml`](config/obi.yml) file:

    idspace: OBI
    base_url: /obo/obi

    products:
    - obi.owl: http://svn.code.sf.net/p/obi/code/releases/2015-09-15/obi.owl

    term_browser: ontobee
    example_terms:
    - OBI_0000070

    entries:
    - exact: /wiki
      replacement: http://obi-ontology.org

Most of these fields are straightforward, but the `entries:` need some more explanation.


### Entries

Each YAML configuration file contains the keyword `entries:` followed by a list of entries. Each entry defines an Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch) directive for matching URLs and redirecting to new URLs. Every entry begins with a `- `, followed by keywords and values on indented lines. There are three types of entries:

1. **exact**: The simplest entry matches an exact URL and returns an exact replacement
2. **prefix**: These entries match the first part of a URL and replace just that prefix part
3. **regex**: These entries use powerful regular expressions, and should be avoided unless absolutely necessary.

The `#` character indicates a comment, which is not considered part of the configuration.

See the [`tools/examples/test2/test2.yml`](tools/examples/test2/test2.yml) and [`tools/examples/test2/test2.htaccess`](tools/examples/test2/test2.htaccess) for examples.


#### Exact

In the most common case, your PURL should match a unique URL and redirect to a unique URL. Here's an example from the `config/obi.yml` file:

    - exact: /obi.owl
      replacement: http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl

This entry will match exactly the URL `http://purl.obolibrary.org/obo/obi/obi.owl`, and it will redirect to exactly `http://svn.code.sf.net/p/obi/code/releases/2015-10-20/obi.owl`. The matched domain name is fixed `http://purl.obolibrary.org`; the next part is project-specific `/obo/obi/`; the final part is taken from the entry `/obi.owl`. The replacement is expected to be a valid, absolute URL, starting with `http`.

Behind the scenes, the entry is translated into a case insensitive Apache RedirectMatch directive in `obo/obi/.htaccess` by escaping special characters and "anchoring" with initial `^`, the project's base URL, and final `$`:

    RedirectMatch temp "(?i)^/2015\-09\-15/obi\.owl$" "http://svn.code.sf.net/p/obi/code/releases/2015-09-15/obi.owl"


#### Prefix

You can also match and replace just the first part of a URL, leaving the rest unchanged. This allows you to define one entry that redirects many URLs matching a common prefix. Another example from `config/obi.yml`:

    - prefix: /branches/
      replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/

This entry will match the URL `http://purl.obolibrary.org/obo/obi/branches/obi.owl` (for example), replace the first part `http://purl.obolibrary.org/obo/obi/branches/` with `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/`, resulting in `http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/obi.owl`. Effectively, the `obi.owl` is appended to the replacement.

The translation is similar, with the addition of `(.*)` wildcard and a `$1` "backreference" at the ends of the given strings:

    RedirectMatch temp "(?i)^/branches/(.*)$" "http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/$1"


#### Regex

Regular expression entries should only be needed very rarely, and should always be used very carefully.

For the regular expression type, the value of the `regex:` and `replacement:` keywords should contain regular expressions in exactly the format expected by Apache [RedirectMatch](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#redirectmatch). The values will be quoted, but no other changes will be made to them. Consider using `(?i)` to make the match case insensitive.


#### Tests

Every `prefix` or `regex` entry should also have a `tests:` keyword, with a list of additional URLs to check. Each test requires a `from:` value (like `exact:`) and a `to:` value (like `replacement:`). Here's an example:

    - prefix: /branches/
      replacement: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/
      tests:
      - from: /branches/obi.owl
        to: http://obi.svn.sourceforge.net/svnroot/obi/trunk/src/ontology/branches/obi.owl


#### Order of Entries

Apache RedirectMatch directives are processed in the [order that they appear](https://httpd.apache.org/docs/2.4/mod/mod_alias.html#order) in the configuration file. Be careful that your `prefix` and `regex` entries do not conflict with your other entries. The YAML-to-Apache translation preserves the order of entries, so you can control the order of processing, but it's best to avoid conflicts.


## Custom Term Browsers

If your project does not use Ontobee or OLS as a term browser, you must specify `term_browser: custom` in your project's YAML configuration file, and provide a `regex` entry in the [`config/obo.yml`](config/obo.yml) configuration file. Here's an example for [ChEBI](https://www.ebi.ac.uk/chebi/):

    # Terms for CHEBI
    - regex: ^/obo/CHEBI_(\d+)$
      replacement: http://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:$1
      tests:
      - from: /CHEBI_15377
        to: http://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377

Note that term redirect rules are case sensitive.

Since these are `regex` entries, and could affect multiple projects, we prefer that OBO admins are the only ones to edit `obo.yml`. If you need a change to the term redirect entry for your project, please [create a new issue](https://github.com/OBOFoundry/purl.obolibrary.org/issues/new).


## Testing and Deployment

We use Docker to test the PURL system locally and deploy it. See the [docker/](https://github.com/OBOFoundry/purl.obolibrary.org/tree/master/docker) directory for code and documentation. Test the system locally like so:

```console
$ docker pull ubuntu:20.04
$ docker build -f docker/Dockerfile -t purl:latest .
$ docker run --rm -it -v "$(pwd)/config":/var/www/purl.obolibrary.org/config purl bash
# sudo su
# cd /var/www/purl.obolibrary.org
# make clean all test
```

To check a single `config/foo.yml` configuration file, run one of these commands

```console
# make clean validate-foo
# make clean build-foo
```

Detailed test results will be listed in `tests/development/*.tsv` files, with their expected and actual values. If you're making changes to the project tools, you can test them against the `tools/examples/` files with:

```console
# make clean test-examples
```


## Copyright

The copyright for the OBO PURL code and documentation belongs to the respective authors. The code is distributed under a [BSD3 license](https://github.com/OBOFoundry/purl.obolibrary.org/blob/master/LICENSE).
