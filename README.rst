Etat Civil
==========

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT
.. image:: https://travis-ci.org/kingsdigitallab/etat-civil-django.svg?branch=develop
    :target: https://travis-ci.org/kingsdigitallab/etat-civil-django
.. image:: https://coveralls.io/repos/github/kingsdigitallab/etat-civil-django/badge.svg?branch=develop
    :target: https://coveralls.io/github/kingsdigitallab/etat-civil-django?branch=develop



For the period 1790-1890, France was the only country to keep systematic (tabular) track of their expatriate citizens
making it possible to study international mobility at scale and in novel ways. The Archives of the French Ministry of
Foreign Affairs hold 120,000 digitised microfilm images of the records from 215 consulates around the world.

The “Etat Civil” -- standing for civil registration of births, deaths and marriages -- is an exploratory project led by
Dr David Todd in collaboration with King’s Digital Lab supported by the Faculty of Arts & Humanities, the Department of
History at King’s College London and the Harvard and Cambridge Centre for History and Economics. The project processes
data from the Egyptian consulate of the “Etat Civil” to visualise mobility on a continental or global scale and offer
insights on patterns of migration and social history more in general.

Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy etat_civil

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html





Deployment
----------

The following details how to deploy this application.



Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html



