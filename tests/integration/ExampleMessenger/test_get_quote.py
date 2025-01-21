from conftest import LZ_ENDPOINT_ID


def test_quote_fee(forked_env, messenger_contract):
    """Test basic quote for default LZ receive option"""
    # Get quote for basic message
    fee = messenger_contract.quote_lz_fee(LZ_ENDPOINT_ID, messenger_contract.address, b"0", 500_000)
    print(f"\nBasic quote fee: {fee}")

    # Should return non-zero fee
    assert fee > 0, "Fee should not be zero"
