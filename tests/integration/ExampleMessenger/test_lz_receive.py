import boa

from conftest import LZ_ENDPOINT_ID, LZ_ENDPOINT_BASE_SEPOLIA


def test_default_behavior(forked_env, messenger_contract, dev_deployer):
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
        LZ_ENDPOINT_ID,  # srcEid
        bytes.fromhex("00" * 12 + dev_deployer[2:]),  # pad 12 bytes of zeros + 20 bytes address
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


def test_message_receiving(forked_env, messenger_contract, dev_deployer):
    """Test regular message receiving"""
    # Setup
    source_chain = LZ_ENDPOINT_ID
    source_address = dev_deployer

    # Set peer for source chain
    messenger_contract.set_peer(source_chain, source_address, sender=dev_deployer)

    # Create test message
    test_message = "Hello from source chain"
    message_bytes = bytes(test_message, "utf-8")

    # Create origin struct for regular message
    origin = (
        source_chain,  # srcEid - regular chain ID
        bytes.fromhex("00" * 12 + dev_deployer[2:]),  # padded address
        1,  # nonce
    )

    # Mock receiving regular message
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        messenger_contract.lzReceive(
            origin,
            bytes(32),  # guid
            message_bytes,
            dev_deployer,  # executor
            b"",  # extraData
        )

    # Check regular message event
    events = messenger_contract.get_logs()
    print("\nRegular message events:", events)
    assert f"MessageReceived(source={source_chain}, payload={test_message}" in repr(events)


def test_read_response_receiving(forked_env, messenger_contract, dev_deployer):
    """Test read response receiving"""
    # Setup
    source_address = dev_deployer

    # Set peer for source chain (read channel)
    read_channel = messenger_contract.LZ_READ_CHANNEL()
    messenger_contract.set_peer(read_channel, source_address, sender=dev_deployer)

    # Create test response
    test_response = "Response from target chain"
    response_bytes = bytes(test_response, "utf-8")

    # Create origin struct for read response
    origin = (
        read_channel,  # srcEid - read channel ID
        bytes.fromhex("00" * 12 + dev_deployer[2:]),  # padded address
        1,  # nonce
    )

    # Mock receiving read response
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        messenger_contract.lzReceive(
            origin,
            bytes(32),  # guid
            response_bytes,
            dev_deployer,  # executor
            b"",  # extraData
        )

    # Check read response event
    events = messenger_contract.get_logs()
    print("\nRead response events:", events)
    assert f"ReadResponseReceived(source={read_channel}, response={test_response}" in repr(events)


def test_receive_authentication(forked_env, messenger_contract, dev_deployer):
    """Test receive authentication checks"""
    source_chain = LZ_ENDPOINT_ID
    source_address = dev_deployer
    test_message = "Test message"
    message_bytes = bytes(test_message, "utf-8")

    origin = (
        source_chain,
        bytes.fromhex("00" * 12 + dev_deployer[2:]),
        1,
    )

    # Try receiving without setting peer
    with boa.reverts("Peer not set"):
        with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
            messenger_contract.lzReceive(
                origin,
                bytes(32),
                message_bytes,
                dev_deployer,
                b"",
            )

    # Set peer but try receiving from wrong endpoint
    messenger_contract.set_peer(source_chain, source_address, sender=dev_deployer)
    with boa.reverts("Not LZ endpoint"):
        messenger_contract.lzReceive(
            origin,
            bytes(32),
            message_bytes,
            dev_deployer,
            b"",
        )

    # Try receiving from wrong peer address
    wrong_origin = (
        source_chain,
        bytes.fromhex("00" * 12 + "1234567890" * 4),  # different address
        1,
    )
    with boa.reverts("Invalid peer"):
        with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
            messenger_contract.lzReceive(
                wrong_origin,
                bytes(32),
                message_bytes,
                dev_deployer,
                b"",
            )
