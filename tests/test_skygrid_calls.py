import unittest

import datetime

import httpretty
import re
from flask import json
from httplib2 import socks
from moto import mock_ec2

from app.definitions.instances.hub import Hub
from app.skygrid_on_demand import SkygridOnDemand


class TestSkygridOnDemand(unittest.TestCase):

    @httpretty.activate
    def setUp(self):
        self.mock_ec2 = mock_ec2()
        self.mock_ec2.start()

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
        self.skygrid_calls = self.skygrid_service.skygrid_calls
    
    def tearDown(self):
        self.mock_ec2.stop()
        
    @httpretty.activate
    def test_get_grid_idle_time(self):
        response = json.loads(
            json.dumps(
                {
                    "nodes": [
                        {
                            "host": "10.101.10.001",
                            "hostname": "SSDVWUK1SEL001",
                            "status": "idle",
                            "idle_time": "150",
                            "busy_time": "0",
                            "browser_active": "false"
                        }
                    ]
                }
            )
        )

        hub = Hub('i-abcdefgh', 'm3.medium', datetime.datetime.now(), '10.41.1.1', 1)
        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_grid_idle_time(hub=hub) == 150

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.002",
                        "hostname": "SSDVWUK1SEL002",
                        "status": "idle",
                        "idle_time": "200",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_grid_idle_time(hub=hub) == 150

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.003",
                        "hostname": "SSDVWUK1SEL003",
                        "status": "idle",
                        "idle_time": "100",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_grid_idle_time(hub=hub) == 100

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.004",
                        "hostname": "SSDVWUK1SEL004",
                        "status": "busy",
                        "idle_time": "0",
                        "busy_time": "50",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_grid_idle_time(hub=hub) == 0

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.005",
                        "hostname": "SSDVWUK1SEL005",
                        "status": "idle",
                        "idle_time": "5",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_grid_idle_time(hub=hub) == 0

    @httpretty.activate
    def test_get_connected_nodes(self):
        response = json.loads(
            json.dumps(
                {
                    "nodes": [
                        {
                            "host": "10.101.10.001",
                            "hostname": "SSDVWUK1SEL001",
                            "status": "idle",
                            "idle_time": "150",
                            "busy_time": "0",
                            "browser_active": "false"
                        }
                    ]
                }
            )
        )

        hub = Hub('i-abcdefgh', 'm3.medium', datetime.datetime.now(), '10.41.1.1', 1)
        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_nodes_connected_to_hub(hub=hub) == ['10.101.10.001']

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.002",
                        "hostname": "SSDVWUK1SEL002",
                        "status": "idle",
                        "idle_time": "200",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_nodes_connected_to_hub(hub=hub) == ['10.101.10.001', '10.101.10.002']

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.003",
                        "hostname": "SSDVWUK1SEL003",
                        "status": "idle",
                        "idle_time": "100",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_nodes_connected_to_hub(hub=hub) == ['10.101.10.001', '10.101.10.002', '10.101.10.003']

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.004",
                        "hostname": "SSDVWUK1SEL004",
                        "status": "busy",
                        "idle_time": "0",
                        "busy_time": "50",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_nodes_connected_to_hub(hub=hub) == ['10.101.10.001', '10.101.10.002', '10.101.10.003', '10.101.10.004']

        response['nodes'].append(
            json.loads(
                json.dumps(
                    {
                        "host": "10.101.10.005",
                        "hostname": "SSDVWUK1SEL005",
                        "status": "idle",
                        "idle_time": "5",
                        "busy_time": "0",
                        "browser_active": "false"
                    }
                )
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_nodes_connected_to_hub(hub=hub) == ['10.101.10.001', '10.101.10.002', '10.101.10.003', '10.101.10.004', '10.101.10.005']

    @httpretty.activate
    def test_is_hub_ready(self):
        response = json.loads(
            json.dumps(
                {
                    "nodes": []
                }
            )
        )
        hub = Hub('i-abcdefgh', 'm3.medium', datetime.datetime.now(), '10.41.1.1', 1)
        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.is_skygrid_ready_on_hub(hub=hub) is False

        response = json.loads(
            json.dumps(
                {
                    "nodes": [
                        {
                            "host": "10.101.10.001",
                            "hostname": "SSDVWUK1SEL001",
                            "status": "idle",
                            "idle_time": "150",
                            "busy_time": "0",
                            "browser_active": "false"
                        }
                    ]
                }
            )
        )

        httpretty.register_uri(httpretty.GET, "http://{0}:4444/grid/admin/ActiveNodeServlet".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.is_skygrid_ready_on_hub(hub=hub) is True

    @httpretty.activate
    def test_served_sessions(self):
        response = json.loads(
            json.dumps(
                {
                  "exit_code": 0,
                  "out": [],
                  "error": [],
                  "today": 8393,
                  "yesterday": 7937,
                  "last_week": 52860,
                  "week_so_far": 43790,
                  "quarter": 8393,
                  "last_quarter": 521932
                }
            )
        )
        hub = Hub('i-abcdefgh', 'm3.medium', datetime.datetime.now(), '10.41.1.1', 1)
        httpretty.register_uri(httpretty.GET, "http://{0}:3000/served_sessions".format(hub.get_ip_address()), body=json.dumps(response))
        assert self.skygrid_calls.get_served_sessions_from_hub(hub=hub) == 530325