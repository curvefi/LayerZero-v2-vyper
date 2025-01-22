import boa

from conftest import LZ_ENDPOINT_ID, LZ_ENDPOINT_BASE_SEPOLIA

GAS_LZ_FEE = 500_000


def test_quote_lz_fee(forked_env, lz_module_contract):
    """Test basic quote for default LZ receive option"""
    # Get quote for basic message
    fee = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {b'0'}, {GAS_LZ_FEE})"
    )
    print(f"\nBasic quote fee: {fee}")

    # Should return non-zero fee
    assert fee > 0, "Fee should not be zero"

    # now compare with external method
    fee_external = lz_module_contract.quote_lz_fee(
        LZ_ENDPOINT_ID, lz_module_contract.address, b"0", GAS_LZ_FEE
    )
    assert fee == fee_external, "Fees should match"


def test_quote_fee_different_receivers(forked_env, lz_module_contract, dev_deployer):
    """Test quotes with different receiver addresses"""
    # Quote to self
    fee_self = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {b'0'}, {GAS_LZ_FEE})"
    )

    # Quote to deployer
    fee_deployer = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {dev_deployer}, {b'0'}, {GAS_LZ_FEE})"
    )

    print(f"\nFee to self: {fee_self}")
    print(f"Fee to deployer: {fee_deployer}")

    # Fees should be similar for different receivers
    assert abs(fee_self - fee_deployer) < fee_self * 0.1, "Fees should be similar"


def test_quote_fee_revert_case(forked_env, lz_module_contract):
    """Test cases where quote should revert"""
    # Invalid chain ID
    with boa.reverts():
        lz_module_contract.eval(
            f"self._quote_lz_fee({0}, {lz_module_contract.address}, {b'0'}, {GAS_LZ_FEE})"
        )


def test_endpoint_interaction(forked_env, lz_module_contract, scan_url, scan_api):
    """Compare contract quote with direct endpoint call"""
    # Get quote via contract
    fee_contract = lz_module_contract.eval(
        f"self._quote_lz_fee({LZ_ENDPOINT_ID}, {lz_module_contract.address}, {b'0'}, {GAS_LZ_FEE})"
    )

    print(f"\nContract quote: {fee_contract}")

    # Get quote directly from endpoint (known working way)
    endpoint = boa.from_etherscan(
        LZ_ENDPOINT_BASE_SEPOLIA,
        uri=scan_url,
        api_key=scan_api,
    )

    # Same message format as working example
    payload = b"0"
    # Use exact same options as docs
    options = bytes.fromhex("0003010011010000000000000000000000000000ea60")
    print(f"Options: 0x{options.hex()}")

    # Create params like working example
    params = (
        LZ_ENDPOINT_ID,  # dstEid
        bytes.fromhex("00" * 32),  # receiver
        payload,  # encoded string
        options,  # vanilla OFT options
        False,  # payInLzToken
    )

    # Get direct quote
    fee_direct = endpoint.quote(params, lz_module_contract.address)
    print("\nDirect quote result:")
    print(f"- Native fee: {fee_direct[0]}")
    print(f"- LZ token fee: {fee_direct[1]}")

    # Compare fees - since we use different messages, they might differ slightly
    assert abs(fee_contract - fee_direct[0]) < fee_contract * 0.1, "Fees differ too much"
