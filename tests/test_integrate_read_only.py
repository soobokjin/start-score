from typing import List

from iconservice.iconscore.icon_score_result import TransactionResult

from tests import create_address, string_to_hex_string
from tests.test_integrate_base import TestIntegrateBase
from iconservice import *


class TestHello(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.score_owner: 'Address' = create_address()
        self.score_address = self.deploy_score("hello", self.score_owner)

    def test_var_db(self):
        expected_value = "test"
        tx_results: List['TransactionResult'] = self.send_tx(self.score_owner,
                                                             self.score_address,
                                                             'setVar',
                                                             {"data": expected_value})

        actual_value = self.query(self.score_address, 'getVar')

        self.assertEqual(expected_value, actual_value)
        self.assertEqual(tx_results[0].event_logs[0].data[0], expected_value)

    def test_dict_db(self):
        tx_results: List['TransactionResult'] = self.send_tx(self.score_owner,
                                                             self.score_address,
                                                             'setDict',
                                                             {"key": "test", "value": "0x1"})

        actual_value = self.query(self.score_address, 'getDict', {"key": "test"})
        self.assertEqual("0x1", actual_value)

    def test_msg(self):
        hex_data: str = string_to_hex_string("test text")
        tx_result = self.send_message(self.score_owner,
                                      self.owner1,
                                      hex_data)
