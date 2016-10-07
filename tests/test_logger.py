import unittest

from app.skygrid_on_demand import SkygridOnDemand
from moto import mock_ec2


class TestSkygridOnDemand(unittest.TestCase):

    @mock_ec2
    def test_logger_operates_correctly(self):
        skygrid_service = SkygridOnDemand(testing_mode=True)
        skygrid_service.logger.info("testing info")
        skygrid_service.logger.warn("testing warn")
        skygrid_service.logger.error("testing error")

        log = skygrid_service.get_log_data()

        substring = "testing error"
        string_line = log[0]
        assert substring in string_line, "Expected: '{0}' to contain '{1}'".format(string_line, substring)
        substring = "testing warn"
        string_line = log[1]
        assert substring in string_line, "Expected: '{0}' to contain '{1}'".format(string_line, substring)
        substring = "testing info"
        string_line = log[2]
        assert substring in string_line, "Expected: '{0}' to contain '{1}'".format(string_line, substring)

if __name__ == '__main__':
    unittest.main()
