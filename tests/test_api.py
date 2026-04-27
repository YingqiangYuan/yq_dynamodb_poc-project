# -*- coding: utf-8 -*-

from yq_dynamodb_poc import api


def test():
    _ = api


if __name__ == "__main__":
    from yq_dynamodb_poc.tests import run_cov_test

    run_cov_test(
        __file__,
        "yq_dynamodb_poc.api",
        preview=False,
    )
