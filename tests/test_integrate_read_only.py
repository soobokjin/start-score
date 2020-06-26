from typing import List

from iconservice.iconscore.icon_score_result import TransactionResult

from tests import create_address, string_to_hex_string
from tests.test_integrate_base import TestIntegrateBase
from iconservice import *


class TestHello(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        # SCORE Owner 생성
        self.score_owner: 'Address' = create_address()
        # Deploy SCORE. parameter로 SCORE의 package name, SCORE Owner 전달
        self.score_address = self.deploy_score("hello", self.score_owner)

    def test_var_db(self):
        expected_value = "test"
        # Send Transaction. return 되는 데이터는 TransactionResult instance 이며 각
        # TransactionResult에는 Transaction 처리 결과가 기록.
        # Eventlog, 처리 결과 등
        tx_result: 'TransactionResult' = self.send_tx(self.score_owner,
                                                      self.score_address,
                                                      'setVar',
                                                      {"data": expected_value})

        # Query를 통해 처리 결과를 확인할 수 있음. return 결과의 type, value는 'icx_call' RPC request의 'response'와 동일
        actual_value = self.query(self.score_address, 'getVar')

        self.assertEqual(expected_value, actual_value)
        self.assertEqual(tx_result.event_logs[0].data[0], expected_value)

    def test_dict_db(self):
        tx_result: 'TransactionResult' = self.send_tx(self.score_owner,
                                                      self.score_address,
                                                      'setDict',
                                                      {"key": "test", "value": "0x1"})

        actual_value = self.query(self.score_address, 'getDict', {"key": "test"})
        self.assertEqual("0x1", actual_value)

    def test_msg(self):
        # message call의 경우 hex string으로 변환해야 하며 'string_to_hex_string' method를 통해 변환 가능
        hex_data: str = string_to_hex_string("test text")
        tx_result = self.send_message(self.score_owner,
                                      self.owner1,
                                      hex_data)
