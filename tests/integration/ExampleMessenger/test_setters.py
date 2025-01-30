import boa
from conftest import LZ_ENDPOINT_ID


def test_owner_functions(forked_env, messenger_contract, dev_deployer):
    """Test owner-only functions"""
    with boa.env.prank(dev_deployer):
        # Test setting peer
        messenger_contract.set_peer(LZ_ENDPOINT_ID, dev_deployer)
        assert messenger_contract.LZ_PEERS(LZ_ENDPOINT_ID) == dev_deployer

        # Test setting gas limit
        new_gas = 1_000_000
        messenger_contract.set_default_gas(new_gas)
        assert messenger_contract.default_gas_limit() == new_gas

        # Test setting read channel
        new_channel = 12345
        messenger_contract.set_lz_read_channel(new_channel)

        # Test setting delegate
        messenger_contract.set_lz_delegate(dev_deployer)
        assert messenger_contract.LZ_DELEGATE() == dev_deployer
