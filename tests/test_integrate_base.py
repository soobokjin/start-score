# -*- coding: utf-8 -*-

# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""IconServiceEngine testcase
"""
from unittest import TestCase

from typing import TYPE_CHECKING, Union, Optional, Any

from iconcommons import IconConfig
from iconservice.base.block import Block
from iconservice.icon_config import default_icon_config
from iconservice.base.address import ZERO_SCORE_ADDRESS
from iconservice.icon_constant import ConfigKey
from iconservice.icon_service_engine import IconServiceEngine
from iconservice.base.address import Address
from tests import create_address, create_tx_hash, create_block_hash
from tests import root_clear, create_timestamp, get_score_path
from tests.in_memory_zip import InMemoryZip

if TYPE_CHECKING:
    from iconservice.base.address import Address, MalformedAddress


class TestIntegrateBase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._score_root_path = '.score'
        cls._state_db_root_path = '.statedb'
        cls._test_sample_root = ""
        cls._signature = "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA="

        cls._version = 3
        cls._step_limit = 1 * 10 ** 9
        cls._icx_factor = 10 ** 18

        cls.admin: 'Address' = create_address()
        cls.genesis: 'Address' = create_address()
        cls.owner1: 'Address' = create_address()
        cls.owner2: 'Address' = create_address()
        cls.owner3: 'Address' = create_address()

        cls._fee_treasury: 'Address' = create_address()

    def setUp(self):
        root_clear(self._score_root_path, self._state_db_root_path)

        self._block_height = 0
        self._prev_block_hash = None

        config = IconConfig("", default_icon_config)
        config.load()
        config.update_conf({ConfigKey.BUILTIN_SCORE_OWNER: str(self.admin)})
        config.update_conf({ConfigKey.SERVICE: {ConfigKey.SERVICE_AUDIT: False,
                                                ConfigKey.SERVICE_FEE: False,
                                                ConfigKey.SERVICE_DEPLOYER_WHITE_LIST: False,
                                                ConfigKey.SERVICE_SCORE_PACKAGE_VALIDATOR: False}})
        config.update_conf({ConfigKey.SCORE_ROOT_PATH: self._score_root_path,
                            ConfigKey.STATE_DB_ROOT_PATH: self._state_db_root_path})
        config.update_conf(self._make_init_config())

        self.icon_service_engine = IconServiceEngine()
        self.icon_service_engine.open(config)

        self._genesis_invoke()

    def tearDown(self):
        self.icon_service_engine.close()
        root_clear(self._score_root_path, self._state_db_root_path)

    def _make_init_config(self) -> dict:
        return {}

    def _genesis_invoke(self) -> list:
        tx_hash = create_tx_hash()
        timestamp_us = create_timestamp()
        request_params = {
            'txHash': tx_hash,
            'version': self._version,
            'timestamp': timestamp_us
        }

        tx = {
            'method': 'icx_sendTransaction',
            'params': request_params,
            'genesisData': {
                "accounts": [
                    {
                        "name": "genesis",
                        "address": self.genesis,
                        "balance": 100 * self._icx_factor
                    },
                    {
                        "name": "fee_treasury",
                        "address": self._fee_treasury,
                        "balance": 0
                    },
                    {
                        "name": "owner1",
                        "address": self.owner1,
                        "balance": 100 * self._icx_factor
                    },
                    {
                        "name": "owner2",
                        "address": self.owner2,
                        "balance": 100 * self._icx_factor
                    },
                    {
                        "name": "owner3",
                        "address": self.owner3,
                        "balance": 100 * self._icx_factor
                    },
                ]
            },
        }

        block_hash = create_block_hash()
        block = Block(self._block_height, block_hash, timestamp_us, None)

        invoke_response, state_root_hash, added_transactions, next_preps = \
            self.icon_service_engine.invoke(block=block,
                                            tx_requests=[tx])

        self.icon_service_engine.commit(block.height, block.hash, None)
        self._block_height += 1
        self._prev_block_hash = block_hash

        return invoke_response

    def deploy_score(self,
                     package_name: str,
                     deployer_address: 'Address',
                     deploy_params: dict = None):
        tx1 = self._make_deploy_tx("",
                                   package_name,
                                   deployer_address,
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params=deploy_params)

        prev_block, tx_results = self._make_and_req_block([tx1])
        self._write_precommit_state(prev_block)

        self.assertEqual(tx_results[0].status, int(True))
        score_address = tx_results[0].score_address

        return score_address

    def _make_deploy_tx(self, score_root: str,
                        score_name: str,
                        addr_from: Union['Address', None],
                        addr_to: 'Address',
                        deploy_params: dict = None,
                        timestamp_us: int = None,
                        data: bytes = None,
                        is_sys: bool = False):

        if deploy_params is None:
            deploy_params = {}

        score_path = get_score_path(score_root, score_name)

        if is_sys:
            deploy_data = {'contentType': 'application/tbears', 'content': score_path, 'params': deploy_params}
        else:
            if data is None:
                mz = InMemoryZip()
                mz.zip_in_memory(score_path)
                data = f'0x{mz.data.hex()}'
            else:
                data = f'0x{bytes.hex(data)}'
            deploy_data = {'contentType': 'application/zip', 'content': data, 'params': deploy_params}

        if timestamp_us is None:
            timestamp_us = create_timestamp()
        nonce = 0

        request_params = {
            "version": self._version,
            "from": addr_from,
            "to": addr_to,
            "stepLimit": self._step_limit,
            "timestamp": timestamp_us,
            "nonce": nonce,
            "signature": self._signature,
            "dataType": "deploy",
            "data": deploy_data
        }

        method = 'icx_sendTransaction'
        # Insert txHash into request params
        request_params['txHash'] = create_tx_hash()
        tx = {
            'method': method,
            'params': request_params
        }

        self.icon_service_engine.validate_transaction(tx)
        return tx

    def query(self, score_address: 'Address', method: str, params: dict = None):
        params = {} if params is None else params
        query_request = {
            "version": self._version,
            "from": self.admin,
            "to": score_address,
            "dataType": "call",
            "data": {
                "method": method,
                "params": params
            }
        }
        return self._query(query_request)

    def send_tx(self,
                addr_from: Optional['Address'],
                addr_to: 'Address',
                method: str,
                params: dict,
                value: int = 0):
        tx = self._make_score_call_tx(addr_from, addr_to, method, params, value)
        prev_block, tx_results = self._make_and_req_block([tx])
        self.assertEqual(int(True), tx_results[0].status)

        self._write_precommit_state(prev_block)
        return tx_results[0]

    def send_message(self,
                     addr_from: Optional['Address'],
                     addr_to: 'Address',
                     data: str,
                     value: int = 0
                     ):
        tx = self._make_score_message_tx(addr_from, addr_to, data, value)
        prev_block, tx_results = self._make_and_req_block([tx])
        self.assertEqual(int(True), tx_results[0].status)

        self._write_precommit_state(prev_block)
        return tx_results[0]

    def _make_score_message_tx(self,
                               addr_from: Optional['Address'],
                               addr_to: 'Address',
                               data: str,
                               value: int = 0):
        timestamp_us = create_timestamp()
        nonce = 0

        request_params = {
            "version": self._version,
            "from": addr_from,
            "to": addr_to,
            "value": value,
            "stepLimit": self._step_limit,
            "timestamp": timestamp_us,
            "nonce": nonce,
            "signature": self._signature,
            "dataType": "message",
            "data": data
        }

        method = 'icx_sendTransaction'
        # Insert txHash into request params
        request_params['txHash'] = create_tx_hash()
        tx = {
            'method': method,
            'params': request_params
        }

        self.icon_service_engine.validate_transaction(tx)
        return tx

    def _make_score_call_tx(self,
                            addr_from: Optional['Address'],
                            addr_to: 'Address',
                            method: str,
                            params: dict,
                            value: int = 0):

        timestamp_us = create_timestamp()
        nonce = 0

        request_params = {
            "version": self._version,
            "from": addr_from,
            "to": addr_to,
            "value": value,
            "stepLimit": self._step_limit,
            "timestamp": timestamp_us,
            "nonce": nonce,
            "signature": self._signature,
            "dataType": "call",
            "data": {
                "method": method,
                "params": params
            }
        }

        method = 'icx_sendTransaction'
        # Insert txHash into request params
        request_params['txHash'] = create_tx_hash()
        tx = {
            'method': method,
            'params': request_params
        }

        self.icon_service_engine.validate_transaction(tx)
        return tx

    def icx_send_tx(self,
                    addr_from: Optional['Address'],
                    addr_to: Union['Address', 'MalformedAddress'],
                    value: int, disable_pre_validate: bool = False,
                    support_v2: bool = False):
        tx = self._make_icx_send_tx(addr_from, addr_to, value, support_v2)
        prev_block, tx_results = self._make_and_req_block([tx])
        self.assertEqual(tx_results[0].status, int(True))

        self._write_precommit_state(prev_block)
        return tx_results

    def _make_icx_send_tx(self,
                          addr_from: Optional['Address'],
                          addr_to: Union['Address', 'MalformedAddress'],
                          value: int, disable_pre_validate: bool = False,
                          support_v2: bool = False):

        timestamp_us = create_timestamp()
        nonce = 0

        request_params = {
            "from": addr_from,
            "to": addr_to,
            "value": value,
            "stepLimit": self._step_limit,
            "timestamp": timestamp_us,
            "nonce": nonce,
            "signature": self._signature
        }

        if support_v2:
            request_params["fee"] = 10 ** 16
        else:
            request_params["version"] = self._version

        method = 'icx_sendTransaction'
        # Insert txHash into request params
        request_params['txHash'] = create_tx_hash()
        tx = {
            'method': method,
            'params': request_params
        }

        if not disable_pre_validate:
            self.icon_service_engine.validate_transaction(tx)
        return tx

    def _make_and_req_block(self, tx_list: list, block_height: int = None) -> tuple:
        if block_height is None:
            block_height: int = self._block_height
        block_hash = create_block_hash()
        timestamp_us = create_timestamp()

        block = Block(block_height, block_hash, timestamp_us, self._prev_block_hash)

        tx_results, state_root_hash, added_transactions, next_preps = \
            self.icon_service_engine.invoke(block=block,
                                            tx_requests=tx_list)
        return block, tx_results

    def _write_precommit_state(self, block: 'Block') -> None:
        self.icon_service_engine.commit(block.height, block.hash, None)
        self._block_height += 1
        self._prev_block_hash = block.hash

    def _remove_precommit_state(self, block: 'Block') -> None:
        self.icon_service_engine.rollback(block.height, block.hash)

    def _query(self, request: dict, method: str = 'icx_call') -> Any:
        response = self.icon_service_engine.query(method, request)
        return response

    def _create_invalid_block(self, block_height: int = None) -> 'Block':
        if block_height is None:
            block_height: int = self._block_height
        block_hash = create_block_hash()
        timestamp_us = create_timestamp()

        return Block(block_height, block_hash, timestamp_us, self._prev_block_hash)
