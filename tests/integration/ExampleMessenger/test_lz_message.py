from conftest import LZ_ENDPOINT_ID
import boa

GAS_LZ_FEE = 500_000
TEST_MESSAGE = "Hello LayerZero!"


def test_quote_message_fee(forked_env, messenger_contract):
    """Test basic quote for regular message sending"""
    # Get quote for string message
    fee = messenger_contract.quote_message_fee(
        LZ_ENDPOINT_ID, messenger_contract.address, TEST_MESSAGE, GAS_LZ_FEE
    )
    print(f"\nBasic message quote fee: {fee}")

    # Should return non-zero fee
    assert fee > 0, "Fee should not be zero"


def test_send_message(forked_env, messenger_contract, dev_deployer):
    """Test sending regular message"""
    boa.env.evm.set_balance(dev_deployer, 10**18)  # 1 ETH
    # Quote the required fee

    balance_before = boa.env.evm.get_balance(dev_deployer)
    assert balance_before == 10**18

    # Get quote first
    required_fee = messenger_contract.quote_message_fee(
        LZ_ENDPOINT_ID, messenger_contract.address, TEST_MESSAGE, GAS_LZ_FEE
    )

    # Send message with quoted fee
    _ = messenger_contract.send_message(
        LZ_ENDPOINT_ID,
        messenger_contract.address,
        TEST_MESSAGE,
        GAS_LZ_FEE,
        value=3 * required_fee,
        sender=dev_deployer,
    )
    balance_after = boa.env.evm.get_balance(dev_deployer)
    assert balance_after > balance_before - 3 * required_fee  # assert refund

    # Check event
    events = messenger_contract.get_logs()
    assert f"MessageSent(destination={LZ_ENDPOINT_ID}, payload={TEST_MESSAGE}" in repr(
        events
    )  # no fee check because string comparison
