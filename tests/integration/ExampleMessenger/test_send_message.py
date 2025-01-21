import boa

from conftest import LZ_ENDPOINT_ID


def test_default_behavior(forked_env, messenger_contract, dev_deployer):
    """
    Test successful message sending with sufficient fee
    """
    boa.env.evm.set_balance(dev_deployer, 10**18)  # 1 ETH
    # Quote the required fee
    required_fee = messenger_contract.quote_lz_fee(LZ_ENDPOINT_ID, dev_deployer, b"0" * 50, 500_000)

    balance_before = boa.env.evm.get_balance(dev_deployer)
    assert balance_before == 10**18
    # Send message with correct fee
    messenger_contract.send_message(
        LZ_ENDPOINT_ID,
        dev_deployer,
        "hello lz",
        500_000,
        value=int(0.5 * 10**18),  # large value! expecting a refund!
        sender=dev_deployer,
    )
    balance_after = boa.env.evm.get_balance(dev_deployer)
    assert balance_after > balance_before - 3 * required_fee  # assert refund
