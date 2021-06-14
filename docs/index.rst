.. Merit documentation master file, created by
   sphinx-quickstart on Sat Jun 12 18:47:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Merit's documentation!
=================================

.. toctree::
   :maxdepth: 2

   source/modules


Getting Started
=================================

Visit https://developer.merits.com to create an app and receive your ``app_id`` and ``app_secret``.


Installation
=================================

``pip install merit``

**Create a Merit object with:**

``m = merit.Merit(app_id, app_secret)``

If you are testing or running on Sandbox, pass the ``production=False`` param:

``m =  merit.Merit(app_id, app_secret, production=False)``

**Create an Org object with:**

``o = merit.Org(app_id, app_secret, org_id, production=False)``

**Read all support methods here:**

:py:mod:`merit`
:py:mod:`org`


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
