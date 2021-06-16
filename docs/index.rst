Welcome to Merit's documentation!
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
