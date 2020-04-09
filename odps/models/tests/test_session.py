#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 1999-2019 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import json
import time
import random
import textwrap
from datetime import datetime, timedelta

import requests

from odps.tests.core import TestBase, to_str, tn, pandas_case
from odps.compat import unittest, six
from odps.models import Instance, SQLTask, Schema, session
from odps.errors import ODPSError
from odps import errors, compat, types as odps_types, utils, options

TEST_SESSION_WORKERS = 4
TEST_SESSION_WORKER_MEMORY = 512

TEST_TABLE_NAME = "_pyodps__session_test_table"
TEST_CREATE_SCHEMA = Schema.from_lists(['id'], ['bigint'])
TEST_UPDATE_STRING = "insert into table %s select count(*) from %s" % (TEST_TABLE_NAME, TEST_TABLE_NAME)
TEST_SELECT_STRING = "select * from %s" % TEST_TABLE_NAME


class Test(TestBase):

    def testCreateSession(self):
        sess_instance = self.odps.create_session(TEST_SESSION_WORKERS, TEST_SESSION_WORKER_MEMORY)
        self.assertTrue(sess_instance)
        # wait to running
        try:
            while sess_instance.status != Instance.Status.RUNNING:
                pass
        except ODPSError as ex:
            print("LOGVIEW: " + sess_instance.get_logview_address())
            print("Task results: " + str(sess_instance.get_task_results()))
            raise ex
        # the status should keep consistent
        self.assertTrue(sess_instance.status == Instance.Status.RUNNING)
        # finally stop it.
        sess_instance.stop()

    def testAttachSession(self):
        sess_instance = self.odps.create_session(TEST_SESSION_WORKERS, TEST_SESSION_WORKER_MEMORY)
        self.assertTrue(sess_instance)
        # wait to running
        try:
            while sess_instance.status != Instance.Status.RUNNING:
                pass
        except ODPSError as ex:
            print("LOGVIEW: " + sess_instance.get_logview_address())
            print("Task results: " + str(sess_instance.get_task_results()))
            raise ex
        # the status should keep consistent
        self.assertTrue(sess_instance.status == Instance.Status.RUNNING)
        att_instance = self.odps.attach_session(sess_instance._session_name)
        self.assertTrue(att_instance)
        # wait to running
        try:
            while att_instance.status != Instance.Status.RUNNING:
                pass
        except ODPSError as ex:
            print("LOGVIEW: " + att_instance.get_logview_address())
            print("Task results: " + str(att_instance.get_task_results()))
            raise ex
        # the status should keep consistent
        self.assertTrue(att_instance.status == Instance.Status.RUNNING)
        # finally stop it.
        sess_instance.stop()

    def testSessionSQL(self):
        self.odps.delete_table(TEST_TABLE_NAME, if_exists=True)
        table = self.odps.create_table(TEST_TABLE_NAME, TEST_CREATE_SCHEMA)
        self.assertTrue(table)
        sess_instance = self.odps.create_session(TEST_SESSION_WORKERS, TEST_SESSION_WORKER_MEMORY)
        self.assertTrue(sess_instance)
        # wait to running
        try:
            while sess_instance.status != Instance.Status.RUNNING:
                pass
        except ODPSError as ex:
            print("LOGVIEW: " + sess_instance.get_logview_address())
            print("Task Result:" + str(sess_instance.get_task_results()))
            raise ex
        # the status should keep consistent
        self.assertTrue(sess_instance.status == Instance.Status.RUNNING)
        inst = sess_instance.run_sql(TEST_UPDATE_STRING)
        inst.wait_for_completion()
        self.assertTrue(inst.status == Instance.Status.TERMINATED)
        self.assertRaises(errors.ODPSError, lambda: inst.open_reader())
        self.assertRaises(errors.ODPSError, lambda: inst.open_reader(tunnel=True))
        select_inst = sess_instance.run_sql(TEST_SELECT_STRING)
        select_inst.wait_for_completion()
        rows = []
        try:
            with select_inst.open_reader(tunnel=True) as rd:
                for each_row in rd:
                    rows.append(each_row.values)
        except BaseException as ex:
            print("LOGVIEW: " + select_inst.get_logview_address())
            print("Task Result:" + str(select_inst.get_task_results()))
            raise ex
        self.assertTrue(len(rows) == 1)
        self.assertTrue(len(rows[0]) == 1)
        self.assertTrue(int(rows[0][0]) == 0)
        # OK, close
        sess_instance.stop()
        self.odps.delete_table(TEST_TABLE_NAME, if_exists=True)

if __name__ == '__main__':
    unittest.main()