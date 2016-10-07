import datetime
import random
import re
import unittest

import httpretty
from app.skygrid_on_demand import SkygridOnDemand
from flask import json
from httplib2 import socks
from moto import mock_ec2
from xmlrpclib import MAXINT, MININT

from app import config
from tests.sample_responses import SERVED_SESSIONS


class TestSkygridOnDemand(unittest.TestCase):

    def setUp(self):
        self.mock_ec2 = mock_ec2()
        self.mock_ec2.start()
        self.httpretty = httpretty
        self.httpretty.activate

        socks.socket.setdefaulttimeout(1)
        
        # Prevent calls to non-existent nodes that just timeout
        httpretty.register_uri(
            httpretty.GET,
            re.compile("http://[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\:3000/stop_grid"),
            body="stop_grid",
        )

        httpretty.register_uri(
            httpretty.GET,
            re.compile("http://[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\:3000/start_grid"),
            body="start_grid",
        )

        httpretty.register_uri(
            httpretty.GET,
            re.compile("http://[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\:3000/reset"),
            body="reset",
        )

        httpretty.register_uri(
            httpretty.GET,
            re.compile("http://[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\:3000/set_hub"),
            body="set_hub",
        )
        
        self.skygrid_service = SkygridOnDemand(testing_mode=True)

    def tearDown(self):
        self.mock_ec2.stop()
        self.httpretty.disable

    def test_allocate_grid_raises_assertion_for_string_input(self):
        for i in range(1000):
            with self.assertRaises(AssertionError):
                length = random.randint(0, 100)
                nodes_str = ''.join(chr(int(random.random() * 96 + 32)) for _ in range(length))
                self.skygrid_service.allocate_grid(number_of_nodes=nodes_str, team='tas_testing')

    def test_allocate_grid_raises_assertion_for_input_below_range(self):
        with self.assertRaises(AssertionError):
                self.skygrid_service.allocate_grid(number_of_nodes=0, team='tas_testing')

        for i in range(100):
            with self.assertRaises(AssertionError):
                num_nodes = random.randint(-100, 0)
                self.skygrid_service.allocate_grid(number_of_nodes=num_nodes, team='tas_testing')

        for i in range(1000):
            with self.assertRaises(AssertionError):
                num_nodes = random.randint(MININT, -1000)
                self.skygrid_service.allocate_grid(number_of_nodes=num_nodes, team='tas_testing')

    def test_allocate_grid_raises_assertion_for_input_above_range(self):
        with self.assertRaises(AssertionError):
                self.skygrid_service.allocate_grid(number_of_nodes=config.MAX_NUMBER_OF_NODES+1, team='tas_testing')

        for i in range(100):
            with self.assertRaises(AssertionError):
                num_nodes = random.randint(config.MAX_NUMBER_OF_NODES+1, 1000)
                self.skygrid_service.allocate_grid(number_of_nodes=num_nodes, team='tas_testing')

        for i in range(1000):
            with self.assertRaises(AssertionError):
                num_nodes = random.randint(1000, MAXINT)
                self.skygrid_service.allocate_grid(number_of_nodes=num_nodes, team='tas_testing')

    def test_allocate_grid_raises_assertion_for_invalid_teams(self):
        with self.assertRaises(AssertionError):
                self.skygrid_service.allocate_grid(number_of_nodes=1, team='')

        for i in range(1000):
            with self.assertRaises(AssertionError):
                length = random.randint(1, config.MIN_TEAM_LENGTH - 1)
                team_str = ''.join(chr(int(random.random() * 96 + 32)) for _ in range(length))
                self.skygrid_service.allocate_grid(number_of_nodes=1, team=team_str)

    def test_allocate_grid_does_not_raise_assertion_for_valid_request(self):
        self.skygrid_service.allocate_grid(number_of_nodes=1, team='tas_testing')
        self.skygrid_service.allocate_grid(number_of_nodes=config.MAX_NUMBER_OF_NODES, team='tas_testing')

    def test_assign_nodes_to_hub(self):
        old_hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=5)
        new_hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=5)
        nodes = self.skygrid_service.spinup_nodes(number_of_nodes=5, hub=old_hub)

        assert len(old_hub.get_nodes()) == 5
        assert len(new_hub.get_nodes()) == 0

        self.skygrid_service.assign_nodes_to_hub(nodes, new_hub)

        assert len(new_hub.get_nodes()) == 5
        assert new_hub.get_nodes() == nodes

    def test_finish_hub(self):
        hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=2)

        assert self.skygrid_service.hub_pool.get_pool_size() == 0

        self.skygrid_service.finish_with_hub(hub)

        assert self.skygrid_service.hub_pool.get_pool_size() == 1

        assert hub.get_nodes() == []
        assert hub.get_requested_node_size() == 0

    def test_finish_node(self):
        hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        node = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]

        assert self.skygrid_service.node_pool.get_pool_size() == 0

        self.skygrid_service.finish_with_node(node)

        assert self.skygrid_service.node_pool.get_pool_size() == 1

    def test_auto_teardown(self):
        hub_55 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_56 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_57 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_58 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_59 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)

        nodes = self.skygrid_service.spinup_nodes(number_of_nodes=5, hub=hub_56)
        node_55 = nodes[0]
        node_56 = nodes[1]
        node_57 = nodes[2]
        node_58 = nodes[3]
        node_59 = nodes[4]

        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub_55.get_ip_address()), body=SERVED_SESSIONS)
        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub_56.get_ip_address()), body=SERVED_SESSIONS)
        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub_57.get_ip_address()), body=SERVED_SESSIONS)
        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub_58.get_ip_address()), body=SERVED_SESSIONS)
        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub_59.get_ip_address()), body=SERVED_SESSIONS)

        self.skygrid_service.finish_with_hub(hub_55)
        self.skygrid_service.finish_with_hub(hub_56)
        self.skygrid_service.finish_with_hub(hub_57)
        self.skygrid_service.finish_with_hub(hub_58)
        self.skygrid_service.finish_with_hub(hub_59)

        self.skygrid_service.finish_with_node(node_55)
        self.skygrid_service.finish_with_node(node_56)
        self.skygrid_service.finish_with_node(node_57)
        self.skygrid_service.finish_with_node(node_58)
        self.skygrid_service.finish_with_node(node_59)

        mins_ago_55 = datetime.datetime.utcnow() - datetime.timedelta(minutes=55)
        mins_ago_56 = datetime.datetime.utcnow() - datetime.timedelta(minutes=56)
        mins_ago_57 = datetime.datetime.utcnow() - datetime.timedelta(minutes=57)
        mins_ago_58 = datetime.datetime.utcnow() - datetime.timedelta(minutes=58)
        mins_ago_59 = datetime.datetime.utcnow() - datetime.timedelta(minutes=59)

        node_55.creation_time = mins_ago_55
        hub_55.creation_time = mins_ago_55
        node_56.creation_time = mins_ago_56
        hub_56.creation_time = mins_ago_56
        node_57.creation_time = mins_ago_57
        hub_57.creation_time = mins_ago_57
        node_58.creation_time = mins_ago_58
        hub_58.creation_time = mins_ago_58
        node_59.creation_time = mins_ago_59
        hub_59.creation_time = mins_ago_59

        assert node_55.get_time_until_hour() == 5
        assert hub_55.get_time_until_hour() == 5
        assert node_56.get_time_until_hour() == 4
        assert hub_56.get_time_until_hour() == 4
        assert node_57.get_time_until_hour() == 3
        assert hub_57.get_time_until_hour() == 3
        assert node_58.get_time_until_hour() == 2
        assert hub_58.get_time_until_hour() == 2
        assert node_59.get_time_until_hour() == 1
        assert hub_59.get_time_until_hour() == 1

        assert self.skygrid_service.hub_pool.get_pool_size() == 5
        assert self.skygrid_service.node_pool.get_pool_size() == 5

        self.skygrid_service.off_to_the_cloud_in_the_sky()

        assert hub_55 in self.skygrid_service.hub_pool.list_all()
        assert hub_56 in self.skygrid_service.hub_pool.list_all()
        assert hub_57 not in self.skygrid_service.hub_pool.list_all()
        assert hub_58 not in self.skygrid_service.hub_pool.list_all()
        assert hub_59 in self.skygrid_service.hub_pool.list_all()

        assert node_55 in self.skygrid_service.node_pool.list_all()
        assert node_56 in self.skygrid_service.node_pool.list_all()
        assert node_57 not in self.skygrid_service.node_pool.list_all()
        assert node_58 not in self.skygrid_service.node_pool.list_all()
        assert node_59 in self.skygrid_service.node_pool.list_all()

        assert self.skygrid_service.hub_pool.get_pool_size() == 3, self.skygrid_service.hub_pool.get_pool_size()
        assert self.skygrid_service.node_pool.get_pool_size() == 3, self.skygrid_service.node_pool.get_pool_size()

    def test_finish_grid(self):
        # self.skygrid_service = SkygridOnDemand(testing_mode=True)
        hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=5)
        nodes = self.skygrid_service.spinup_nodes(number_of_nodes=5, hub=hub)

        assert self.skygrid_service.hub_pool.get_pool_size() == 0
        assert self.skygrid_service.node_pool.get_pool_size() == 0

        assert hub.get_nodes() == nodes
        assert hub.get_requested_node_size() == 5

        self.skygrid_service.finish_with_grid(hub.get_instance_id())

        assert self.skygrid_service.hub_pool.get_pool_size() == 1
        assert self.skygrid_service.node_pool.get_pool_size() == 5

        assert hub.get_nodes() == []
        assert hub.get_requested_node_size() == 0

    # @unittest.skip("Skipping 'test_report' - Permissions issue")
    def test_report(self):
        report = json.loads(json.dumps(self.skygrid_service.dump_report()))

        assert report['active_grids'] == []
        assert report['pooled_hubs'] == []
        assert report['pooled_nodes'] == []
        assert report['active_grids_count'] == 0
        assert report['pooled_hubs_count'] == 0
        assert report['pooled_nodes_count'] == 0

        grid_1 = self.skygrid_service.allocate_grid(5,'tas_harnesses')
        grid_2 = self.skygrid_service.allocate_grid(5,'tas_harnesses')
        grid_3 = self.skygrid_service.allocate_grid(5,'tas_harnesses')
        grid_4 = self.skygrid_service.allocate_grid(5,'tas_harnesses')
        grid_5 = self.skygrid_service.allocate_grid(5,'tas_harnesses')

        self.skygrid_service.finish_with_grid(grid_1)
        self.skygrid_service.finish_with_grid(grid_2)

        report = json.loads(json.dumps(self.skygrid_service.dump_report()))

        assert report['active_grids'] != []
        assert report['pooled_hubs'] != []
        assert report['pooled_nodes'] != []
        assert report['active_grids_count'] == 3
        assert report['pooled_hubs_count'] == 2
        assert report['pooled_nodes_count'] == 10

    # @unittest.skip("Skipping 'test_refresh_registry' - Permissions issue")
    def test_refresh_registry(self):
        grid_1 = self.skygrid_service.allocate_grid(1,'tas_harnesses')
        grid_2 = self.skygrid_service.allocate_grid(2, 'tas_harnesses')
        grid_3 = self.skygrid_service.allocate_grid(3, 'tas_harnesses')
        grid_4 = self.skygrid_service.allocate_grid(4, 'tas_harnesses')
        grid_5 = self.skygrid_service.allocate_grid(5, 'tas_harnesses')

        self.skygrid_service.finish_with_grid(grid_4)

        self.skygrid_service.finish_with_grid(grid_3)

        self.skygrid_service_2 = SkygridOnDemand(testing_mode=True)
        report_1 = json.loads(json.dumps(self.skygrid_service.dump_report()))

        report_2 = json.loads(json.dumps(self.skygrid_service_2.dump_report()))
        for active_grid in report_1['active_grids']:
            active_grid['assigned_seconds'] = 0
        for hub in report_1['pooled_hubs']:
            hub['assigned_seconds'] = 0
        for active_grid in report_2['active_grids']:
            active_grid['assigned_seconds'] = 0
        for hub in report_2['pooled_hubs']:
            hub['assigned_seconds'] = 0

        self.assertEqual(ordered(report_1), ordered(report_2))

    # @unittest.skip("Skipping 'test_pools_dont_duplicate' - Permissions issue")
    def test_pools_dont_duplicate(self):

        grid_id = self.skygrid_service.allocate_grid(1, 'tas_harnesses')

        assert self.skygrid_service.hub_pool.get_pool_size() == 0
        assert self.skygrid_service.node_pool.get_pool_size() == 0

        self.skygrid_service.finish_with_grid(grid_id)

        assert self.skygrid_service.hub_pool.get_pool_size() == 1
        assert self.skygrid_service.node_pool.get_pool_size() == 1

        self.skygrid_service.finish_with_grid(grid_id)

        assert self.skygrid_service.hub_pool.get_pool_size() == 1
        assert self.skygrid_service.node_pool.get_pool_size() == 1

    def test_abandoned_logic(self):
        # Any grid with idle time == 0 is running tests - not abandoned
        assert not self.skygrid_service.is_grid_abandoned(idle_time=0, assigned_time=0)
        assert not self.skygrid_service.is_grid_abandoned(idle_time=0, assigned_time=299)
        assert not self.skygrid_service.is_grid_abandoned(idle_time=0, assigned_time=1000)

        # A pooled grid will have a high idle time, but low assigned time
        # Do not consider abandoned until 5 minutes after assignment
        assert not self.skygrid_service.is_grid_abandoned(idle_time=400, assigned_time=0)
        assert not self.skygrid_service.is_grid_abandoned(idle_time=699, assigned_time=299)

        # If idle for more than 5 minutes, check if assignment was more than 5 minutes ago
        assert self.skygrid_service.is_grid_abandoned(idle_time=300, assigned_time=360)
        assert self.skygrid_service.is_grid_abandoned(idle_time=300, assigned_time=1000)
        assert self.skygrid_service.is_grid_abandoned(idle_time=1000, assigned_time=360)
        assert self.skygrid_service.is_grid_abandoned(idle_time=1000, assigned_time=1000)

    def test_hub_pool(self):
        hub_pool = self.skygrid_service.hub_pool

        assert hub_pool.get_pool_size() == 0
        assert hub_pool.get_pooled_hub('m3.medium') is None

        hub_1 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_2 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_3 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_4 = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)
        hub_5 = self.skygrid_service.spinup_hub(instance_type='m3.large', number_of_nodes=1)

        mins_left_10 = datetime.datetime.utcnow() - datetime.timedelta(minutes=50)
        mins_left_20 = datetime.datetime.utcnow() - datetime.timedelta(minutes=40)
        mins_left_30 = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        mins_left_40 = datetime.datetime.utcnow() - datetime.timedelta(minutes=20)
        mins_left_50 = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

        hub_1.creation_time = mins_left_30
        hub_2.creation_time = mins_left_40
        hub_3.creation_time = mins_left_10
        hub_4.creation_time = mins_left_50
        hub_5.creation_time = mins_left_20

        hub_pool.add_to_pool(hub_1)
        hub_pool.add_to_pool(hub_2)
        hub_pool.add_to_pool(hub_3)
        hub_pool.add_to_pool(hub_4)
        hub_pool.add_to_pool(hub_5)

        assert hub_pool.get_pool_size() == 5

        hub = hub_pool.get_pooled_hub("m3.medium")
        assert hub_pool.get_pool_size() == 4
        assert hub.get_time_until_hour() == 10

        hub = hub_pool.get_pooled_hub("m3.medium")
        assert hub_pool.get_pool_size() == 3
        assert hub.get_time_until_hour() == 30

        hub = hub_pool.get_pooled_hub("m3.large")
        assert hub_pool.get_pool_size() == 2
        assert hub.get_time_until_hour() == 20

        hub = hub_pool.get_pooled_hub("m3.medium")
        assert hub_pool.get_pool_size() == 1
        assert hub.get_time_until_hour() == 40

        hub = hub_pool.get_pooled_hub("m3.medium")
        assert hub_pool.get_pool_size() == 0
        assert hub.get_time_until_hour() == 50

    def test_node_pool(self):
        node_pool = self.skygrid_service.node_pool

        assert node_pool.get_pool_size() == 0
        assert node_pool.get_pooled_node() is None

        hub = self.skygrid_service.spinup_hub(instance_type='m3.medium', number_of_nodes=1)

        node_1 = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]
        node_2 = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]
        node_3 = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]
        node_4 = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]
        node_5 = self.skygrid_service.spinup_nodes(number_of_nodes=1, hub=hub)[0]

        mins_left_10 = datetime.datetime.utcnow() - datetime.timedelta(minutes=50)
        mins_left_20 = datetime.datetime.utcnow() - datetime.timedelta(minutes=40)
        mins_left_30 = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        mins_left_40 = datetime.datetime.utcnow() - datetime.timedelta(minutes=20)
        mins_left_50 = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

        node_1.creation_time = mins_left_30
        node_2.creation_time = mins_left_40
        node_3.creation_time = mins_left_10
        node_4.creation_time = mins_left_50
        node_5.creation_time = mins_left_20

        node_pool.add_to_pool(node_1)
        node_pool.add_to_pool(node_2)
        node_pool.add_to_pool(node_3)
        node_pool.add_to_pool(node_4)
        node_pool.add_to_pool(node_5)

        assert node_pool.get_pool_size() == 5

        nodes = node_pool.get_pooled_nodes(number_of_nodes=1)
        assert node_pool.get_pool_size() == 4
        assert nodes[0].get_time_until_hour() == 10

        nodes = node_pool.get_pooled_nodes(number_of_nodes=3)
        assert node_pool.get_pool_size() == 1
        assert nodes[0].get_time_until_hour() == 20
        assert nodes[1].get_time_until_hour() == 30
        assert nodes[2].get_time_until_hour() == 40

        nodes = node_pool.get_pooled_nodes(number_of_nodes=1)
        assert node_pool.get_pool_size() == 0
        assert nodes[0].get_time_until_hour() == 50


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

if __name__ == '__main__':
    unittest.main()
