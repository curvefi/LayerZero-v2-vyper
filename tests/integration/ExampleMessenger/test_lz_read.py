import boa

import boa.util
import boa.util.abi
from conftest import LZ_ENDPOINT_ID
from vyper.utils import method_id


def test_default_behavior(forked_env, messenger_contract, dev_deployer):
    """Test lzRead request sending"""
    # # Setup
    # source_endpoint = LZ_ENDPOINT_ID
    # source_address = messenger_contract.address

    # # Set peer for source chain
    # messenger_contract.set_peer(source_endpoint, source_address, sender=dev_deployer)
    # Quote the required fee
    #     def quote_read_fee(
    #     _dst_eid: uint32,
    #     _target: address,
    #     _calldata: Bytes[128],
    #     _gas_limit: uint256 = 0,
    #     _data_size: uint32 = 64,
    # ) -> uint256:

    source_endpoint = LZ_ENDPOINT_ID
    source_address = messenger_contract.address
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
    # Quote the required fee
    required_fee = messenger_contract.quote_read_fee(source_endpoint, source_address, calldata2)
    print(f"Required fee: {required_fee}")
    assert required_fee > 0, "Fee should not be zero"

    boa.env.evm.set_balance(dev_deployer, 10**18)  # 1 ETH
    balance_before = boa.env.evm.get_balance(dev_deployer)
    assert balance_before == 10**18
    # Send message with correct fee
    messenger_contract.request_lzRead(
        source_endpoint, source_address, calldata2, sender=dev_deployer, value=int(0.5 * 10**18)
    )
    balance_after = boa.env.evm.get_balance(dev_deployer)
    assert balance_after > balance_before - 3 * required_fee  # assert refund
