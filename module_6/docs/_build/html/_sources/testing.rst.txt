Testing Guide
=============

Markers
-------
All tests are marked with one or more of:

- web
- buttons
- analysis
- db
- integration

Run suite
---------
.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration"

Selectors
---------
- ``data-testid="pull-data-btn"``
- ``data-testid="update-analysis-btn"``
