import json
import re
import unittest

import httpretty
from httplib2 import socks
from moto import mock_ec2


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

        self.headers = {"Content-type": "application/json"}

        api_service.application.config['TESTING'] = True

        # This needs to go here to configure it before importing the service

        self.appl = api_service.application.test_client()

    def tearDown(self):
        self.mock_ec2.stop()
        self.httpretty.disable

    # @unittest.skip("Skipping 'test_allocate_grid_returns_hub_id_when_valid_parameters_are_passed' - No AMI visibility")
    def test_allocate_grid_returns_hub_id_when_valid_parameters_are_passed(self):
        rv = self.appl.post('/new', data=json.dumps({"team": "test", "nodes": 1}), headers=self.headers)
        assert json.loads(rv.data)['hub_id'].startswith("i-")
        assert rv.status_code == 200

    def test_allocate_grid_returns_400_when_called_with_invalid_content_type(self):
        rv = self.appl.post('/new', data={"team": "test", "nodes": 1}, headers={"Content-type": "application/text"})
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_when_team_parameter_is_an_empty_string(self):
        rv = self.appl.post('/new', data={"team": "", "nodes": 1}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_when_team_parameter_is_not_passed(self):
        rv = self.appl.post('/new', data={"nodes": 1}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_when_team_parameter_is_none(self):
        rv = self.appl.post('/new', data={"team": None, "nodes": 1}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_when_node_parameter_is_not_passed(self):
        rv = self.appl.post('/new', data={"team": "test"}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_error_when_number_of_nodes_passed_more_than_100(self):
        rv = self.appl.post('/new', data={"team": "test", "nodes": 101}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_400_error_when_number_of_nodes_passed_is_0(self):
        rv = self.appl.post('/new', data={"team": "test", "nodes": 0}, headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_json_header(self):
        rv = self.appl.post('/new', data=json.dumps({"team": "test", "nodes": 1}), headers=self.headers)
        assert rv.headers["Content-type"] == "application/json"

    def test_allocate_grid_returns_400_when_no_parameters_are_passed(self):
        rv = self.appl.post('/new', data=json.dumps({}), headers=self.headers)
        assert rv.status_code == 400

    def test_allocate_grid_returns_405_when_called_with_wrong_http_method(self):
        rv = self.appl.get('/new', data=json.dumps({}), headers=self.headers)
        assert rv.status_code == 405

    # @unittest.skip("Skipping 'test_status_grid_returns_skygrid_ready_status_when_valid_instance_id_is_passed' - No AMI visibility")
    def test_status_grid_returns_skygrid_ready_status_when_valid_instance_id_is_passed(self):
        rv = self.appl.post('/new', data=json.dumps({"team": "test", "nodes": 1}), headers=self.headers)
        hub_id = json.loads(rv.data)['hub_id']
        status = self.appl.get('/status/'+hub_id).data
        self.assertIn(json.loads(status)["skygrid_status"], ["SKYGRID_REGISTERING", "SKYGRID_READY"])

    def test_status_grid_returns_400_when_invalid_instance_id_is_passed(self):
        rv = self.appl.get('/status/invalid')
        assert rv.status_code == 404
        self.assertEqual(json.loads(rv.data)["skygrid_status"], "INSTANCE_NOT_FOUND")

    # @unittest.skip("Skipping 'test_status_grid_returns_ip_when_valid_instance_id_is_passed' - No AMI visibility")
    def test_status_grid_returns_ip_when_valid_instance_id_is_passed(self):
        rv = self.appl.post('/new', data=json.dumps({"team": "test", "nodes": 1}), headers=self.headers)
        hub_id = json.loads(rv.data)['hub_id']
        status = self.appl.get('/status/'+hub_id).data
        assert re.match("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", json.loads(status)['hub_ip'])

    def test_status_grid_returns_an_empty_ip__when_invalid_instance_id_is_passed(self):
        status = self.appl.get('/status/invalid').data
        self.assertEqual(json.loads(status)['hub_ip'], "")

    def test_report_endpoint_returns_empty_report(self):
        data = self.appl.get('/report').data
        report = json.loads(data)['report']

        self.assertIn('active_grids', report)
        self.assertIn('active_grids_count', report)
        self.assertIn('pooled_hubs', report)
        self.assertIn('pooled_hubs_count', report)
        self.assertIn('pooled_nodes', report)
        self.assertIn('pooled_nodes_count', report)

    def test_log_endpoint_returns_log_data(self):
        data = self.appl.get('/log').data
        log = json.loads(data)['log']

        self.assertIsInstance(log, list)
        for entry in log:
            # Assert each entry is timestamped
            self.assertRegexpMatches(entry, "^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} )")

    def test_refresh_endpoint_returns_empty_report(self):
        data = self.appl.get('/refresh').data
        report = json.loads(data)['report']

        self.assertIn('active_grids', report)
        self.assertIn('active_grids_count', report)
        self.assertIn('pooled_hubs', report)
        self.assertIn('pooled_hubs_count', report)
        self.assertIn('pooled_nodes', report)
        self.assertIn('pooled_nodes_count', report)

    # @unittest.skip("Skipping 'test_finish_deletes_instance_when_valid_id_is_passed' - No AMI visibility")
    def test_finish_deletes_instance_when_valid_id_is_passed(self):
        rv = self.appl.post('/new', data=json.dumps({"team": "123", "nodes": 1}), headers=self.headers)
        hub_id = json.loads(rv.data)['hub_id']
        assert self.appl.delete('/finish/'+hub_id).status_code == 204

if __name__ == '__main__':
    unittest.main()
