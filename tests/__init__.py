#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from shutil import rmtree
from time import time

import hashlib
import os
import random
import sys

from iconcommons.logger import Logger
from iconservice.base.address import Address, AddressPrefix
from iconservice.icon_constant import DATA_BYTE_ORDER

TEST_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))


def get_score_path(score_root: str, package_name: str):
    return os.path.join(TEST_ROOT_PATH, score_root, package_name)


def root_clear(score_path: str, state_db_path: str):
    rmtree(score_path, ignore_errors=True)
    rmtree(state_db_path, ignore_errors=True)


def create_timestamp():
    return int(time() * 10 ** 6)


def create_address(prefix: int = 0, data: bytes = None) -> 'Address':
    if data is None:
        data = create_tx_hash()
    hash_value = hashlib.sha3_256(data).digest()
    return Address(AddressPrefix(prefix), hash_value[-20:])


def create_hash_256(data: bytes = None) -> bytes:
    if data is None:
        max_int = sys.maxsize
        length = (max_int.bit_length() + 7) // 8
        data = int(random.randint(0, max_int)).to_bytes(length, DATA_BYTE_ORDER)

    return hashlib.sha3_256(data).digest()


def create_tx_hash(data: bytes = None) -> bytes:
    return create_hash_256(data)


def create_block_hash(data: bytes = None) -> bytes:
    return create_tx_hash(data)


def raise_exception_start_tag(tag: str = ""):
    emblem_str = '=' * 20
    Logger.error(f'{emblem_str} [{tag}] raise exception start {emblem_str}')


def raise_exception_end_tag(tag: str = ""):
    emblem_str = '=' * 20
    Logger.error(f'{emblem_str} [{tag}] raise exception end {emblem_str}')


def string_to_hex_string(string: str):
    if not isinstance(string, str):
        raise ValueError(f"Invalid type. Only str type can be converted: {type(string)}")

    b_str = string.encode('utf-8')
    return "0x" + b_str.hex()


def hex_string_to_string(hex_string: str):
    if not hex_string.startswith("0x"):
        raise ValueError(f"String should be hex {hex_string}")

    return bytes.fromhex(hex_string[2:]).decode('utf-8')
