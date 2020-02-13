État Civil
==========

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT
.. image:: https://travis-ci.org/kingsdigitallab/etat-civil-django.svg
    :target: https://travis-ci.org/kingsdigitallab/etat-civil-django
.. image:: https://coveralls.io/repos/github/kingsdigitallab/etat-civil-django/badge.svg
    :target: https://coveralls.io/github/kingsdigitallab/etat-civil-django
.. image:: https://readthedocs.org/projects/etat-civil-django/badge/?version=latest
    :target: https://etat-civil-django.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
    :target: https://github.com/pydanny/cookiecutter-django/
    :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
    :alt: Black code style


For the period 1790-1890, France was the only country to keep systematic
(tabular) track of their expatriate citizens making it possible to study
international mobility at scale and in novel ways. The Archives of the French
Ministry of Foreign Affairs hold 120,000 digitised microfilm images of the
records from 215 consulates around the world.

The "État Civil" -- standing for civil registration of births, deaths and
marriages -- is an exploratory project led by `Dr David Todd`_ in collaboration
with `King's Digital Lab`_ supported by the Faculty of Arts & Humanities, the
Department of History at `King's College London`_ and the
`Harvard and Cambridge Centre for History and Economics`_. The project
processes data from the Egyptian consulate of the "État Civil" to visualise
mobility on a continental or global scale and offer insights on patterns of
migration and social history more in general.

.. _Dr David Todd: https://www.kcl.ac.uk/people/david-todd
.. _King's Digital Lab: https://kdl.kcl.ac.uk/
.. _King's College London: https://www.kcl.ac.uk/
.. _Harvard and Cambridge Centre for History and Economics: https://histecon.fas.harvard.edu/

Settings
--------

See detailed `cookiecutter-django settings documentation`_.

.. _cookiecutter-django settings documentation: http://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/settings.html

Running
-------

Getting Started on a Mac
~~~~~~~~~~~~~~~~~~~~~~~~

Install Developer Tools, in a Terminal window::

    $ xcode-select --install

Install and start Docker_.

Clone the repository, https://github.com/kingsdigitallab/etat-civil-django, in
a Terminal window, for example::

    $ cd Documents
    $ git clone https://github.com/kingsdigitallab/etat-civil-django.git
    $ cd etat-civil-django

Start the project::

    $ compose/bin/d_up.sh

Create a superuser, in a different Terminal window, inside the Etat Civil
project::

    $ compose/bin/manage.sh createsuperuser

To import data via the browser the data processing worker needs to be running,
start it with::

    $  compose/bin/manage.sh rqworker default

The project should be available at http://localhost:8000/. Go to
http://localhost:8000/admin/deeds/data/ to import a new Excel file. The
import process might take a few minutes to import all the data in the
spreadsheet.

See also the more detailed
`cookiecutter-django development with Docker documentation`_.

.. _Docker: https://www.docker.com/
.. _cookiecutter-django development with Docker documentation: https://cookiecutter-django-kingsdigitallab.readthedocs.io/en/latest/developing-locally-docker.html

Basic Commands
--------------

Setting Up Your Users
~~~~~~~~~~~~~~~~~~~~~

* To create a **normal user account**, just go to Sign Up and fill out the
  form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go
  to your console to see a simulated email verification message. Copy the link
  into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ compose/bin/manage.sh createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your
superuser logged in on Firefox (or similar), so that you can see how the site
behaves for both kinds of users.

Type checks
~~~~~~~~~~~

Running type checks with mypy:

::

  $ mypy {{cookiecutter.project_slug}}

Test coverage
~~~~~~~~~~~~~

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest
