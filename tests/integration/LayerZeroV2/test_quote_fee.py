import boa
import time
from conftest import LZ_ENDPOINT_ID, LZ_ENDPOINT_BASE_SEPOLIA, LZ_READ_CHANNEL

GAS_LZ_FEE = 500_000
TEST_CALLDATA = bytes.fromhex("aabbcc")


def test_quote_regular_message(forked_env, lz_module_contract):
    """Test basic quote for regular message sending"""
    # Get quote for basic message using internal function
    fee = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, b'0', {GAS_LZ_FEE})"
    )
    print(f"\nBasic message quote fee: {fee}")

    # Should return non-zero fee
    assert fee > 0, "Fee should not be zero"


def test_quote_read_message(forked_env, lz_module_contract):
    """Test quote for read message"""
    # Prepare read message bytes
    message = lz_module_contract.eval(
        f"self._prepare_read_message_bytes({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {TEST_CALLDATA}, False, 0, 15)"
    )

    # Get quote using prepared message
    fee = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_READ_CHANNEL}, {lz_module_contract.address}, {message}, {GAS_LZ_FEE}, 0, 128)"
    )

    print(f"\nRead message quote fee: {fee}")
    assert fee > 0, "Fee should not be zero"


def test_quote_fee_revert_case(forked_env, lz_module_contract):
    """Test cases where quote should revert"""
    # Invalid chain ID
    with boa.reverts():
        lz_module_contract.eval(
            f"self._quote_lz_fee(0, {lz_module_contract.address}, b'0', {GAS_LZ_FEE})"
        )


def test_endpoint_interaction(forked_env, lz_module_contract, scan_url, scan_api):
    """Compare contract quote with direct endpoint call"""
    # Get quote via internal function
    fee_contract = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, b'0', {GAS_LZ_FEE})"
    )

    print(f"\nContract quote: {fee_contract}")

    # Get quote directly from endpoint
    endpoint = boa.from_etherscan(
        LZ_ENDPOINT_BASE_SEPOLIA,
        uri=scan_url,
        api_key=scan_api,
    )

    # Create messaging params like in contract
    options = bytes.fromhex("0003010011010000000000000000000000000000ea60")
    params = (
        LZ_ENDPOINT_ID,
        bytes.fromhex("00" * 32),
        b"0",
        options,
        False,
    )

    # Get direct quote
    fee_direct = endpoint.quote(params, lz_module_contract.address)
    print("\nDirect quote result:")
    print(f"- Native fee: {fee_direct[0]}")
    print(f"- LZ token fee: {fee_direct[1]}")

    # Compare fees
    assert abs(fee_contract - fee_direct[0]) < fee_contract * 0.3, "Fees differ too much"


def test_read_message_preparation(forked_env, lz_module_contract):
    """Test read message preparation"""
    current_time = int(time.time())

    # Test with different parameters
    message1 = lz_module_contract.eval(
        f"self._prepare_read_message_bytes({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {TEST_CALLDATA})"
    )

    message2 = lz_module_contract.eval(
        f"self._prepare_read_message_bytes({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {TEST_CALLDATA}, "
        f"True, {current_time}, 20)"
    )

    assert message1 != message2, "Messages should be different"
    assert len(message1) > 0 and len(message2) > 0, "Messages should not be empty"


def test_gas_limit_handling(forked_env, lz_module_contract):
    """Test handling of gas limits"""
    # Test with default gas limit
    fee1 = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, b'0')"
    )

    # Test with custom gas limit
    fee2 = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, b'0', {GAS_LZ_FEE * 2})"
    )

    assert fee2 > fee1, "Higher gas limit should result in higher fee"
