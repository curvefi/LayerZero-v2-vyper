"""Test OAppRead functionality for OApp."""

import boa
from conftest import _to_bytes32, LZ_READ_CHANNEL


def test_set_read_channel_activate(oapp_module_contract, dev_deployer):
    """Test activating a read channel."""
    # Set up test data
    test_channel_id = LZ_READ_CHANNEL
    self_as_bytes32 = _to_bytes32(oapp_module_contract.address)

    # Initially should be empty/zero
    assert oapp_module_contract.peers(test_channel_id) == _to_bytes32("0x" + "00" * 20)

    # Activate the read channel as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(test_channel_id, True)

    # Verify channel is set with self address (indicating it's active)
    assert oapp_module_contract.peers(test_channel_id) == self_as_bytes32


def test_set_read_channel_deactivate(oapp_module_contract, dev_deployer):
    """Test deactivating a read channel."""
    # Set up test data
    test_channel_id = LZ_READ_CHANNEL
    self_as_bytes32 = _to_bytes32(oapp_module_contract.address)

    # First activate the read channel
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(test_channel_id, True)

    # Verify channel is active
    assert oapp_module_contract.peers(test_channel_id) == self_as_bytes32

    # Now deactivate the read channel
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(test_channel_id, False)

    # Verify channel is deactivated (set to empty address)
    assert oapp_module_contract.peers(test_channel_id) == _to_bytes32("0x" + "00" * 20)


def test_multiple_read_channels(oapp_module_contract, dev_deployer):
    """Test activating multiple read channels."""
    # Set up test data for multiple channels
    channel_ids = [LZ_READ_CHANNEL - i for i in range(3)]
    self_as_bytes32 = _to_bytes32(oapp_module_contract.address)

    # Activate multiple read channels
    for channel_id in channel_ids:
        with boa.env.prank(dev_deployer):
            oapp_module_contract.setReadChannel(channel_id, True)

    # Verify all channels are active
    for channel_id in channel_ids:
        assert oapp_module_contract.peers(channel_id) == self_as_bytes32

    # Deactivate one channel
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(channel_ids[1], False)

    # Verify specific channel is deactivated
    assert oapp_module_contract.peers(channel_ids[1]) == _to_bytes32("0x" + "00" * 20)

    # Verify other channels remain active
    assert oapp_module_contract.peers(channel_ids[0]) == self_as_bytes32
    assert oapp_module_contract.peers(channel_ids[2]) == self_as_bytes32


def test_unauthorized_read_channel_setting(oapp_module_contract):
    """Test that unauthorized users cannot set read channels."""
    # Generate unauthorized user
    unauthorized_user = boa.env.generate_address()
    test_channel_id = LZ_READ_CHANNEL

    # Attempt to set read channel as non-owner
    with boa.env.prank(unauthorized_user):
        with boa.reverts("ownable: caller is not the owner"):
            oapp_module_contract.setReadChannel(test_channel_id, True)


def test_read_channel_event_emission(oapp_module_contract, dev_deployer):
    """Test that PeerSet event is emitted when setting a read channel."""
    test_channel_id = LZ_READ_CHANNEL
    self_as_bytes32 = _to_bytes32(oapp_module_contract.address)

    # Set read channel
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(test_channel_id, True)

    # Verify event emission
    events = oapp_module_contract.get_logs()
    assert any(
        "PeerSet" in str(event)
        and str(test_channel_id) in str(event)
        and str(self_as_bytes32).lower() in str(event).lower()
        for event in events
    ), "PeerSet event not emitted with correct parameters when activating read channel"

    # Deactivate read channel
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(test_channel_id, False)

    # Verify event emission for deactivation
    events = oapp_module_contract.get_logs()
    empty_bytes32 = _to_bytes32("0x" + "00" * 20)
    assert any(
        "PeerSet" in str(event)
        and str(test_channel_id) in str(event)
        and str(empty_bytes32).lower() in str(event).lower()
        for event in events
    ), "PeerSet event not emitted with correct parameters when deactivating read channel"


def test_read_channel_threshold_compatibility(oapp_module_contract, dev_deployer):
    """Test that read channels work correctly with the READ_CHANNEL_THRESHOLD constant."""
    # Extract READ_CHANNEL_THRESHOLD from contract
    read_channel_threshold = oapp_module_contract.eval("OApp.READ_CHANNEL_THRESHOLD")

    # Test channel IDs around the threshold
    below_threshold = read_channel_threshold - 10
    above_threshold = read_channel_threshold + 10

    # Channels above threshold should be valid for read operations
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(above_threshold, True)

    # Verify above threshold channel is properly set
    self_as_bytes32 = _to_bytes32(oapp_module_contract.address)
    assert oapp_module_contract.peers(above_threshold) == self_as_bytes32

    # Below threshold should also work since setReadChannel doesn't check for threshold
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setReadChannel(below_threshold, True)

    # Verify below threshold channel is properly set
    assert oapp_module_contract.peers(below_threshold) == self_as_bytes32
