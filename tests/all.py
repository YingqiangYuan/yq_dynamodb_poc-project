# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from yq_dynamodb_poc.tests import run_cov_test

    run_cov_test(
        __file__,
        "yq_dynamodb_poc",
        is_folder=True,
        preview=False,
    )
