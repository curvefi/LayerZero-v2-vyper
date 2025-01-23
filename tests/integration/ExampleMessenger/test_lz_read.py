import boa

import boa.util
import boa.util.abi
from conftest import LZ_ENDPOINT_ID
from vyper.utils import method_id

GAS_LZ_FEE = 500_000
TEST_CALLDATA = bytes.fromhex("aabbcc")


def test_quote_read_fee(forked_env, messenger_contract):
    """Test quote for read request"""
    fee = messenger_contract.quote_read_fee(
        LZ_ENDPOINT_ID,
        messenger_contract.address,
        TEST_CALLDATA,
        GAS_LZ_FEE,
        64,  # default response size
    )
    print(f"\nRead request quote fee: {fee}")
    assert fee > 0, "Fee should not be zero"


def test_request_read(forked_env, messenger_contract, dev_deployer):
    """Test sending read request"""
    # Get quote first
    fee = messenger_contract.quote_read_fee(
        LZ_ENDPOINT_ID, messenger_contract.address, TEST_CALLDATA, GAS_LZ_FEE
    )
    boa.env.evm.set_balance(dev_deployer, 10**18)  # 1 ETH

    # Send read request
    _ = messenger_contract.request_read(
        LZ_ENDPOINT_ID,
        messenger_contract.address,
        TEST_CALLDATA,
        GAS_LZ_FEE,
        64,
        value=2 * fee,
        sender=dev_deployer,
    )

    # Check event
    events = messenger_contract.get_logs()
    assert (
        f"ReadRequestSent(destination={LZ_ENDPOINT_ID}, target={messenger_contract.address}, payload={TEST_CALLDATA}"
        in repr(events)
    )


def test_prepare_calldata():
    # prepare calldata (in two ways that match)
    method_str = "dummy_endpoint(uint256)"
    num = 12345
    calldata = method_id(method_str) + boa.util.abi.abi_encode("(uint256)", (num,))
    # print(f"\nCalldata from boa.util: {calldata.hex()}")

    dummy_contract = boa.loads(f"""
@external
@view
def tmp()-> Bytes[256]:
    inp: uint256 = {num}
    return abi_encode(inp, method_id=method_id({repr(method_str)}))
""")
    calldata2 = dummy_contract.tmp()
    print(f"Calldata from vyper mock: {calldata2.hex()}")
    assert calldata == calldata2
