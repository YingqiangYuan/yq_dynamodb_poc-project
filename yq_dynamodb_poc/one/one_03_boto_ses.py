# -*- coding: utf-8 -*-

import typing as T
from functools import cached_property

import boto3
from boto_session_manager import BotoSesManager

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_01_main import One


class OneBotoSesMixin:
    @cached_property
    def bsm(self: "One") -> BotoSesManager:
        bsm = BotoSesManager(
            profile_name="yuan_yingqiang_dev",
            region_name="us-east-1",
        )
        return bsm

    @cached_property
    def boto_ses(self: "One") -> boto3.Session:
        return self.bsm.boto_ses

    @cached_property
    def dynamodb_client(self: "One"):
        return self.bsm.dynamodb_client
