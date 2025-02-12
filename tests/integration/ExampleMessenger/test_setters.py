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


def test_set_libs(forked_env, messenger_contract, dev_deployer):
    SEND_LIB = "0xC1868e054425D378095A003EcbA3823a5D0135C9"
    RECEIVE_LIB = "0x12523de19dc41c91F7d2093E0CFbB76b17012C8d"
    READ_LIB = "0x29270F0CFC54432181C853Cd25E2Fb60A68E03f2"

    with boa.env.prank(dev_deployer):
        # Test setting libraries
        messenger_contract.set_lz_send_lib(messenger_contract.address, LZ_ENDPOINT_ID, SEND_LIB)
        messenger_contract.set_lz_receive_lib(
            messenger_contract.address, LZ_ENDPOINT_ID, RECEIVE_LIB
        )
        read_channel = messenger_contract.LZ_READ_CHANNEL()
        print(f"\nRead channel: {read_channel}")
        messenger_contract.set_lz_send_lib(messenger_contract.address, read_channel, READ_LIB)


def test_set_uln(forked_env, messenger_contract, dev_deployer):
    SEND_LIB = "0xC1868e054425D378095A003EcbA3823a5D0135C9"
    # RECEIVE_LIB = "0x12523de19dc41c91F7d2093E0CFbB76b17012C8d"
    # READ_LIB = "0x29270F0CFC54432181C853Cd25E2Fb60A68E03f2"
    # CONFIG_TYPE_READ_LID_CONFIG = 1
    CONFIG_TYPE_ULN = 2
    dvns = [
        "0xbf6ff58f60606edb2f190769b951d825bcb214e2",
        "0xd9222cc3ccd1df7c070d700ea377d4ada2b86eb5",
        "0xdf04abb599c7b37dd5ffc0f8e94f6898120874ef",
        "0xe1a12515f9ab2764b887bf60b923ca494ebbb2d6",
    ]
    with boa.env.prank(dev_deployer):
        messenger_contract.set_lz_uln_config(
            LZ_ENDPOINT_ID,
            messenger_contract.address,
            SEND_LIB,
            CONFIG_TYPE_ULN,
            1,  # confirmations
            [dvns[0]],
            [],
            0,  # optional threshold
        )
