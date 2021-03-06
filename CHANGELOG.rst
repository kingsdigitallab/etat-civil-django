.. :changelog:

Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_, and this project adheres to
`Semantic Versioning`_.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

[0.5.0] - 2020-07-02
--------------------

Added
~~~~~
* Text under data model, workflow, architecture and design process.
* Image under workflow.


[0.4.1] - 2020-05-13
--------------------

Fixed
~~~~~
* Export to GeoJSON.


[0.4.0] - 2020-04-20
--------------------

Added
~~~~~
* Latest version of the data

Changed
~~~~~~~
* Use the place names from the data collection spreasheet rather than the geonames names

Fixed
~~~~~
* Recover deleted test data
* Increase gunicorn timeout for data exports


[0.3.1] - 2020-04-06
--------------------

Fixed
~~~~~
* Add missing dependencies for production
* Database set up on production

[0.3.0] - 2020-04-06
--------------------

Added
~~~~~
* LDAP configuration for production

Changed
~~~~~~~
* Production settings for deployment

[0.2.0] - 2020-03-27
--------------------

Added
~~~~~
* Team information to the docs
* humans.txt (http://humanstxt.org/)
* Docker script to  stop the containers
* Data to source control

[0.1.0] - 2020-02-13
--------------------

Added
~~~~~
* Data model and data collection template
* Django admin interface
* Commands to import/export data into CSV and GeoJSON
* Geocoding workflow
* Map visualisations (wip)
