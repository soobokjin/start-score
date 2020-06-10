from tests import create_address
from tests.test_integrate_base import TestIntegrateBase
from iconservice import *


class TestHello(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.score_owner: 'Address' = create_address()
        self.score_address = self.deploy_score("hello", self.score_owner)

    def test_var_db(self):
        expected_value = "test"
        tx_result = self.send_tx(self.score_owner,
                                 self.score_address,
                                 'setVar',
                                 {"data": expected_value})

        actual_value = self.query(self.score_address, 'getVar')
        self.assertEqual(actual_value, expected_value)