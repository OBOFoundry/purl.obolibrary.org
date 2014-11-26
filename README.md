obo-purls
=========

This is a quick demonstration of an alternative way to manage OBO Foundry PURLs. Like <https://github.com/perma-id/w3id.org> we have a repository containing per-directory Apache configuration files (`.htaccess` files), each of which uses `RewriteRule` directives to redirect PURL requests to their proper targets.

The following examples are *NOT permanent URLs* -- the are running on a little server that might disappear at any time. But they show how things work:

- http://url.ontodev.org/obo/OBI_0000070 (and other OBI term IDs) redirect to Ontobee pages: http://www.ontobee.org/browser/rdf.php?o=OBI&iri=http://purl.obolibrary.org/obo/OBI_0000070
- http://url.ontodev.org/obo/obi/2014-08-18/obi_core.owl redirects to a specific version of the OBI Core OWL file on SourceForge: http://svn.code.sf.net/p/obi/code/releases/2014-08-18/obi_core.owl
- http://url.ontodev.org/obo/obi/wiki redirects to the OBI wiki: http://obi-ontology.org

