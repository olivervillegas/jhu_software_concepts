Overview & Setup
================

Environment
-----------
- ``DATABASE_URL`` (required)

Run app
-------
.. code-block:: bash

   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
   python -m src

Run tests
---------
.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration"
