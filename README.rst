
.. .. image:: https://readthedocs.org/projects/yq-dynamodb-poc/badge/?version=latest
    :target: https://yq-dynamodb-poc.readthedocs.io/en/latest/
    :alt: Documentation Status

.. .. image:: https://github.com/YingqiangYuan/yq_dynamodb_poc-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project/actions?query=workflow:CI

.. .. image:: https://codecov.io/gh/YingqiangYuan/yq_dynamodb_poc-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/YingqiangYuan/yq_dynamodb_poc-project

.. .. image:: https://img.shields.io/pypi/v/yq-dynamodb-poc.svg
    :target: https://pypi.python.org/pypi/yq-dynamodb-poc

.. .. image:: https://img.shields.io/pypi/l/yq-dynamodb-poc.svg
    :target: https://pypi.python.org/pypi/yq-dynamodb-poc

.. .. image:: https://img.shields.io/pypi/pyversions/yq-dynamodb-poc.svg
    :target: https://pypi.python.org/pypi/yq-dynamodb-poc

.. .. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project

------

.. .. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://yq-dynamodb-poc.readthedocs.io/en/latest/py-modindex.html

.. .. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/YingqiangYuan/yq_dynamodb_poc-project/issues

.. .. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/yq-dynamodb-poc#files


Welcome to ``yq_dynamodb_poc`` Documentation
==============================================================================

Hands-on POC for `pynamodb <https://pynamodb.readthedocs.io/>`_ +
`pynamodb-session-manager <https://github.com/MacHu-GWU/pynamodb_session_manager-project>`_
against Amazon DynamoDB, organized as a progressive series of runnable
examples. Each folder is focused on one topic and grows from a minimal
end-to-end script up through CRUD, batching, query/scan, conditional
writes, ACID transactions, secondary indexes, and single-table design —
all in a fin-tech credit-card domain consistent with the AxiomCard
parent project.


Examples
------------------------------------------------------------------------------

Top index: `examples/ <examples/>`_  (also includes
`cleanup_all_tables.py <examples/cleanup_all_tables.py>`_, a utility
script that lists and deletes every ``yq_dynamodb_poc_*`` table after
confirmation).

Folders 00 - 08 contain independently runnable scripts; folders
09 - 11 are sequential demos (run ``s01 → s02 → ...``).

* `00-minimal-poc <examples/00-minimal-poc/>`_ — Golden reference: Model + Attribute + Meta + ``use_boto_session``
* `01-attributes <examples/01-attributes/>`_ — Attribute types: scalar, collection, JSON
* `02-table-management <examples/02-table-management/>`_ — ``create_table`` / ``describe_table`` / billing modes
* `03-crud-basic <examples/03-crud-basic/>`_ — ``save`` / ``get`` / ``update`` / ``delete`` / ``refresh``
* `04-batch-operations <examples/04-batch-operations/>`_ — ``batch_write`` / ``batch_get``, unprocessed items
* `05-query-and-scan <examples/05-query-and-scan/>`_ — ``query`` vs ``scan``, pagination, sort + limit
* `06-condition-expression <examples/06-condition-expression/>`_ — Conditional writes, optimistic locking
* `07-transactions <examples/07-transactions/>`_ — ``TransactWrite`` / ``TransactGet``, ACID across items
* `08-gsi-and-lsi <examples/08-gsi-and-lsi/>`_ — Secondary indexes, projections, GSI vs scan cost
* `09-pipeline-metadata-demo <examples/09-pipeline-metadata-demo/>`_ — Composite demo: replicate the AxiomCard Pipeline Metadata table
* `10-single-table-one-to-many <examples/10-single-table-one-to-many/>`_ — Single-table design: classic 1:N (Customer → Card → Transaction)
* `11-single-table-many-to-many <examples/11-single-table-many-to-many/>`_ — Single-table design: M:N three ways (adjacency / GSI inversion / composite GSI)


.. _install:

Install
------------------------------------------------------------------------------

``yq_dynamodb_poc`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install yq-dynamodb-poc

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade yq-dynamodb-poc
