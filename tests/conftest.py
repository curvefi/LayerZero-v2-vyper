import boa
import pytest
import os
from web3 import Web3

BOA_CACHE = False
LZ_ENDPOINT_BASE_SEPOLIA = "0x6EDCE65403992e310A62460808c4b910D972f10f"
LZ_CHAIN_ID = 84532
LZ_ENDPOINT_ID = 40245
LZ_READ_CHANNEL = 4294967294


@pytest.fixture(scope="session")
def drpc_api_key():
    api_key = os.getenv("DRPC_API_KEY")
    assert api_key is not None, "DRPC_API_KEY environment variable not set"
    return api_key


@pytest.fixture(scope="session")
def eth_web3_client(drpc_api_key):
    if drpc_api_key:
        rpc_url = f"https://lb.drpc.org/ogrpc?network=ethereum&dkey={drpc_api_key}"
    else:
        rpc_url = "https://rpc.ankr.com/eth"
    return Web3(Web3.HTTPProvider(rpc_url))


@pytest.fixture()
def dev_deployer():
    return boa.env.generate_address()


@pytest.fixture()
def forked_env(rpc_url):
    """Automatically fork each test with the specified chain."""
    block_to_fork = "latest"
    with boa.swap_env(boa.Env()):
        if BOA_CACHE:
            boa.fork(url=rpc_url, block_identifier=block_to_fork)
        else:
            boa.fork(url=rpc_url, block_identifier=block_to_fork, cache_file=None)
        boa.env.enable_fast_mode()
        yield


@pytest.fixture(scope="session")
def rpc_url():
    return "https://sepolia.base.org"


@pytest.fixture(scope="session")
def scan_api():
    return os.getenv("BASESCAN_API_KEY")


@pytest.fixture(scope="session")
def scan_url():
    return "https://api-sepolia.basescan.org/api"


@pytest.fixture()
def lz_module_contract(dev_deployer):
    with boa.env.prank(dev_deployer):
        return boa.load("contracts/LayerZeroV2.vy", LZ_ENDPOINT_BASE_SEPOLIA, 500_000)


@pytest.fixture()
def messenger_contract(dev_deployer):
    with boa.env.prank(dev_deployer):
        return boa.load("contracts/ExampleMessenger.vy", LZ_ENDPOINT_BASE_SEPOLIA, 500_000)
