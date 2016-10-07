import unittest

import datetime

from app.skygrid_on_demand import SkygridOnDemand
from moto import mock_ec2


class TestSkygridOnDemand(unittest.TestCase):

    @mock_ec2
    def setUp(self):
        self.skygrid_service = SkygridOnDemand(testing_mode=True)
        self.now = datetime.datetime.utcnow().replace(tzinfo=None)
        self.hundred_secs_ago = datetime.datetime.utcnow().replace(tzinfo=None) - datetime.timedelta(seconds=100)

    @mock_ec2
    def test_scheduled_abandoned_check(self):
        self.skygrid_service.abandoned_grid_timestamp = self.now
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['abandoned_check'], 'PASS')

        self.skygrid_service.abandoned_grid_timestamp = self.hundred_secs_ago
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['abandoned_check'], 'FAIL')

    @mock_ec2
    def test_scheduled_node_check(self):
        self.skygrid_service.check_nodes_timestamp = self.now
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['node_check'], 'PASS')

        self.skygrid_service.check_nodes_timestamp = self.hundred_secs_ago
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['node_check'], 'FAIL')

    @mock_ec2
    def test_scheduled_teardown_check(self):
        self.skygrid_service.teardown_timestamp = self.now
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['teardown_check'], 'PASS')

        self.skygrid_service.teardown_timestamp = self.hundred_secs_ago
        self.assertEqual(self.skygrid_service.get_healthcheck()['scheduled_tasks']['teardown_check'], 'FAIL')