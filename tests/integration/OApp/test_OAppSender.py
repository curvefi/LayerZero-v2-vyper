"""Test OAppSender functionality for OApp. This actually tests the OAppExample contract (to simplify options building)"""

import boa
from conftest import _to_bytes32, LZ_ENDPOINT_ID, LZ_READ_CHANNEL


def test_quote_message_fee(messenger_contract, dev_deployer):
    """Test the quote_message_fee method that uses OApp._quote internally."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_message = "Test message"
    test_gas_limit = 500000

    # Set peer as owner to allow quote to work
    with boa.env.prank(dev_deployer):
        messenger_contract.setPeer(test_eid, _to_bytes32(test_receiver))

    # Get quote for message
    fee = messenger_contract.quote_message_fee(
        test_eid, test_receiver, test_message, test_gas_limit
    )

    # Validate fee structure (may be zero in test environment)
    assert isinstance(fee.nativeFee, int), "nativeFee should be an integer"
    assert isinstance(fee.lzTokenFee, int), "lzTokenFee should be an integer"


def test_quote_with_no_peer(messenger_contract):
    """Test that quoting will revert when no peer is set."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_message = "Test message"
    test_gas_limit = 500000

    # Attempt to get quote without setting peer
    with boa.reverts("OApp: no peer"):
        messenger_contract.quote_message_fee(test_eid, test_receiver, test_message, test_gas_limit)


def test_quote_with_pay_in_lz_token(messenger_contract, dev_deployer):
    """Test quote with LZ token payment option."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_message = "Test message"
    test_gas_limit = 500000

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        messenger_contract.setPeer(test_eid, _to_bytes32(test_receiver))

    # Get quote with LZ token payment option
    with boa.reverts():  # must revert because its not enabled
        messenger_contract.quote_message_fee(
            test_eid, test_receiver, test_message, test_gas_limit, 0, True
        )


def test_send_message(messenger_contract, dev_deployer):
    """Test sending a message through the send_message method that uses OApp._lzSend internally."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_message = "Test message"
    test_gas_limit = 500000

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        messenger_contract.setPeer(test_eid, _to_bytes32(test_receiver))

    # Get quote for the fee
    fee = messenger_contract.quote_message_fee(
        test_eid, test_receiver, test_message, test_gas_limit
    )

    # Add ETH to the environment
    boa.env.set_balance(dev_deployer, 10**18)  # 1 ETH

    # Send message with quoted fee (may not actually send in test environment)
    with boa.env.prank(dev_deployer):
        messenger_contract.send_message(
            test_eid,
            test_receiver,
            test_message,
            test_gas_limit,
            0,  # value
            0,  # lz_token_fee
            value=fee.nativeFee * 2,  # Send double the fee to ensure enough
        )

    # Check event emission
    events = messenger_contract.get_logs()
    assert any(
        "MessageSent" in str(event) and str(test_eid) in str(event) and test_message in str(event)
        for event in events
    ), "MessageSent event not emitted with correct parameters"


def test_send_message_no_peer(messenger_contract, dev_deployer):
    """Test that sending without a peer set reverts."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_message = "Test message"
    test_gas_limit = 500000

    # Add ETH to the environment
    boa.env.set_balance(dev_deployer, 10**18)  # 1 ETH

    # Attempt to send message without setting peer
    with boa.env.prank(dev_deployer):
        with boa.reverts("OApp: no peer"):
            messenger_contract.send_message(
                test_eid,
                test_receiver,
                test_message,
                test_gas_limit,
                0,  # value
                0,  # lz_token_fee
                value=1000,  # Some ETH value
            )


def test_quote_read_fee(messenger_contract, dev_deployer):
    """Test the quote_read_fee method that uses OApp._quote internally."""

    # Activate the read channel as owner
    with boa.env.prank(dev_deployer):
        messenger_contract.setReadChannel(LZ_READ_CHANNEL, True)

    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_calldata = b"Test message"
    test_gas_limit = 500_000

    # Get quote for message
    fee = messenger_contract.quote_read_fee(
        LZ_READ_CHANNEL, test_eid, test_receiver, test_calldata, test_gas_limit
    )
    print(fee)
    # Validate fee structure (may be zero in test environment)
    assert isinstance(fee.nativeFee, int), "nativeFee should be an integer"
    assert isinstance(fee.lzTokenFee, int), "lzTokenFee should be an integer"


def test_send_read_request(messenger_contract, dev_deployer):
    """Test the send_read_request method that uses OApp._lzSend internally."""
    # Activate the read channel as owner
    with boa.env.prank(dev_deployer):
        messenger_contract.setReadChannel(LZ_READ_CHANNEL, True)

    test_eid = LZ_ENDPOINT_ID
    test_receiver = messenger_contract.address
    test_calldata = b"Test message"
    test_gas_limit = 500_000

    # Get quote for message
    fee = messenger_contract.quote_read_fee(
        LZ_READ_CHANNEL, test_eid, test_receiver, test_calldata, test_gas_limit
    )
    print(fee)
    # Validate fee structure (may be zero in test environment)
    assert isinstance(fee.nativeFee, int), "nativeFee should be an integer"
    assert isinstance(fee.lzTokenFee, int), "lzTokenFee should be an integer"

    # Add ETH to the environment
    boa.env.set_balance(dev_deployer, 10**18)  # 1 ETH

    # Send message with quoted fee (may not actually send in test environment)
    with boa.env.prank(dev_deployer):
        messenger_contract.request_read(
            LZ_READ_CHANNEL,
            test_eid,
            test_receiver,
            test_calldata,
            test_gas_limit,
            value=fee.nativeFee * 2,
        )
