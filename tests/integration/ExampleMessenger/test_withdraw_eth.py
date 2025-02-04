import boa

GAS_LZ_FEE = 500_000
TEST_MESSAGE = "Hello LayerZero!"


def test_default_behavior(messenger_contract, dev_deployer):
    boa.env.evm.set_balance(messenger_contract.address, 10**18)  # 1 ETH

    assert boa.env.evm.get_balance(dev_deployer) == 0
    with boa.env.prank(dev_deployer):
        messenger_contract.withdraw_eth(boa.env.evm.get_balance(messenger_contract.address))
    assert boa.env.evm.get_balance(dev_deployer) == 10**18
