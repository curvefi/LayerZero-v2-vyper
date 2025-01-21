import boa

from conftest import LZ_ENDPOINT_ID, LZ_ENDPOINT_BASE_SEPOLIA


def test_default_behavior(messenger_contract, dev_deployer):
    """Test message receiving"""
    # Setup
    source_chain = LZ_ENDPOINT_ID
    source_address = dev_deployer

    # Set peer for source chain
    messenger_contract.set_peer(source_chain, source_address, sender=dev_deployer)

    # Create test message
    test_message = "Hello from source chain"
    message_bytes = bytes(test_message, "utf-8")

    # Create origin struct
    origin = (
        source_chain,  # srcEid
        bytes.fromhex("00" * 12 + source_address[2:]),  # pad 12 bytes of zeros + 20 bytes address
        1,  # nonce
    )

    # Mock receiving message
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        messenger_contract.lzReceive(
            origin,  # Origin struct
            bytes(32),  # guid (empty for test)
            message_bytes,  # message
            dev_deployer,  # executor
            b"",  # extraData
        )

    # Check event
    events = messenger_contract.get_logs()
    print(events)
    assert f"MessageReceived(source={source_chain}, payload={test_message}" in repr(events)
