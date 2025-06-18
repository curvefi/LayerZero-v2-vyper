import boa
import pytest
import os
from web3 import Web3
from eth_utils import to_bytes

LZ_ENDPOINT_BASE_SEPOLIA = "0x6EDCE65403992e310A62460808c4b910D972f10f"
LZ_CHAIN_ID = 84532
LZ_ENDPOINT_ID = 40245
LZ_READ_CHANNEL = 4294967295

BOA_CACHE = True


def _to_bytes32(value):
    """Convert a string or address to bytes32 format."""
    if isinstance(value, str) and value.startswith("0x"):
        # Convert hex string to bytes and pad to 32 bytes
        return to_bytes(hexstr=value).rjust(32, b"\x00")
    else:
        # For non-hex strings or other types
        return to_bytes(text=str(value)).rjust(32, b"\x00")


@pytest.fixture(autouse=True)
def better_traces(forked_env, scan_url, scan_api):
    # contains contracts that are not necessarily called
    # but appear in the traces
    contracts = [
        # "0x6EDCE65403992e310A62460808c4b910D972f10f",
        # "0xcFB06A2F39FfDeF4dE68bd1Efa7AED07c525855D",
        # "0x23e7950ED3253Ec45D9FbbbF8Ba30B42d7537f7B",
        # "0xABCE9415ae2c7DF8C37CbdBa73B6C0630Be02AdA",
        # "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3",
        # "0xB4171f3d814cd7E2dbacB533ba550EE0DA919406",
        # "0x8A3D588D9f6AC041476b094f97FF94ec30169d3D",
        # "0x07F5127dDfc5Dd01F2709d3f37a50E0F6C01d797",
        # "0xe67DC0bF6241C71a6609108A15b8976cd78c2109",
        # "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3",
        # "0xB4171f3d814cd7E2dbacB533ba550EE0DA919406",
        # "0x6EDCE65403992e310A62460808c4b910D972f10f",
        # "0xcFB06A2F39FfDeF4dE68bd1Efa7AED07c525855D",
    ]
    for contract in contracts:
        try:
            boa.from_etherscan(contract, uri=scan_url, api_key=scan_api)
        except Exception as e:
            print(f"Error fetching contract {contract}: {e}")


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
    # return "https://sepolia.drpc.org"


@pytest.fixture(scope="session")
def scan_api():
    return os.getenv("BASESCAN_API_KEY")
    # return os.getenv("ETHERSCAN_API_KEY")


@pytest.fixture(scope="session")
def scan_url():
    return "https://api-sepolia.basescan.org/api"
    # return "https://api-sepolia.etherscan.io/api"


@pytest.fixture()
def oapp_module_contract(dev_deployer):
    with boa.env.prank(dev_deployer):
        wrapper_contract = """
        from snekmate.auth import ownable
        from contracts.oapp_vyper import OApp

        initializes: ownable
        initializes: OApp[ownable:=ownable]

        exports: ownable.__interface__
        exports: OApp.__interface__

        @deploy
        def __init__(_endpoint: address):
            ownable.__init__()
            ownable._transfer_ownership(tx.origin)

            OApp.__init__(_endpoint, tx.origin)

        @internal #placeholders for bytecode inclusion
        def placeholders():
            OApp._getPeerOrRevert(0)
            OApp._lzReceive(empty(OApp.Origin), empty(bytes32), empty(Bytes[OApp.MAX_MESSAGE_SIZE]), empty(address), empty(Bytes[OApp.MAX_EXTRA_DATA_SIZE]))
        """
        contract = boa.loads(wrapper_contract, LZ_ENDPOINT_BASE_SEPOLIA)

        return contract


@pytest.fixture()
def messenger_contract(dev_deployer):
    with boa.env.prank(dev_deployer):
        return boa.load("examples/OAppExample.vy", LZ_ENDPOINT_BASE_SEPOLIA)


@pytest.fixture()
def options_builder_contract():
    return boa.load("src/OptionsBuilder.vy")


@pytest.fixture()
def read_cmd_codec_contract():
    return boa.load("src/ReadCmdCodecV1.vy")


@pytest.fixture()
def constants():
    return boa.load("src/VyperConstants.vy")
