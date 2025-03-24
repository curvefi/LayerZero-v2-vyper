"""Test peer management functionality for OApp."""

import boa
from conftest import _to_bytes32


def test_set_peer(oapp_module_contract, dev_deployer):
    """Test basic peer setting functionality"""
    # Set up test data
    test_eid = 1234
    test_peer = _to_bytes32("0x" + "42" * 20)

    # Initially should be empty/zero
    assert oapp_module_contract.peers(test_eid) == _to_bytes32("0x" + "00" * 20)

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Verify peer is set
    assert oapp_module_contract.peers(test_eid) == test_peer


def test_multiple_peers(oapp_module_contract, dev_deployer):
    """Test setting multiple peers"""
    # Set up test data
    peers = [
        (1234, _to_bytes32("0x" + "42" * 20)),
        (5678, _to_bytes32("0x" + "43" * 20)),
        (9012, _to_bytes32("0x" + "44" * 20)),
    ]

    # Set multiple peers
    for eid, peer in peers:
        with boa.env.prank(dev_deployer):
            oapp_module_contract.setPeer(eid, peer)

    # Verify all peers are set
    for eid, peer in peers:
        assert oapp_module_contract.peers(eid) == peer


def test_remove_peer(oapp_module_contract, dev_deployer):
    """Test removing peers"""
    # Set up initial peers
    test_eid_1 = 1234
    test_peer_1 = _to_bytes32("0x" + "42" * 20)
    test_eid_2 = 5678
    test_peer_2 = _to_bytes32("0x" + "43" * 20)

    # Add peers
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid_1, test_peer_1)

    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid_2, test_peer_2)

    # Remove first peer by setting to zero bytes32
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid_1, _to_bytes32("0x" + "00" * 20))

    # Verify peer is removed
    assert oapp_module_contract.peers(test_eid_1) == _to_bytes32("0x" + "00" * 20)
    assert oapp_module_contract.peers(test_eid_2) == test_peer_2


def test_update_peer(oapp_module_contract, dev_deployer):
    """Test updating existing peer"""
    test_eid = 1234
    test_peer_1 = _to_bytes32("0x" + "42" * 20)
    test_peer_2 = _to_bytes32("0x" + "43" * 20)

    # Set initial peer
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer_1)

    assert oapp_module_contract.peers(test_eid) == test_peer_1

    # Update to new peer
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer_2)

    # Verify update
    assert oapp_module_contract.peers(test_eid) == test_peer_2


def test_unauthorized_peer_setting(oapp_module_contract):
    """Test that unauthorized users cannot set peers"""
    # Generate unauthorized user
    unauthorized_user = boa.env.generate_address()
    test_eid = 1234
    test_peer = _to_bytes32("0x" + "42" * 20)

    # Attempt to set peer as non-owner
    with boa.env.prank(unauthorized_user):
        with boa.reverts("ownable: caller is not the owner"):
            oapp_module_contract.setPeer(test_eid, test_peer)


def test_event_emission(oapp_module_contract, dev_deployer):
    """Test that PeerSet event is emitted when setting a peer"""
    test_eid = 1234
    test_peer = _to_bytes32("0x" + "42" * 20)

    # Set peer
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Verify event emission
    events = oapp_module_contract.get_logs()
    assert any(
        "PeerSet" in str(event) and str(test_eid) in str(event) and str(test_peer) in str(event)
        for event in events
    ), "PeerSet event not emitted with correct parameters"


def test_getPeerOrRevert(oapp_module_contract, dev_deployer):
    """Test getPeerOrRevert function"""
    test_eid = 1234
    test_peer = _to_bytes32("0x" + "42" * 20)

    # Check reverts with no peer set
    with boa.reverts("OApp: no peer"):
        oapp_module_contract.eval(f"OApp._getPeerOrRevert({test_eid})")

    # Set peer
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Check peer is returned correctly
    with boa.env.prank(dev_deployer):
        assert oapp_module_contract.eval(f"OApp._getPeerOrRevert({test_eid})") == test_peer

    # Check reverts with peer set to zero bytes32
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, _to_bytes32("0x" + "00" * 20))

    with boa.env.prank(dev_deployer):
        with boa.reverts("OApp: no peer"):
            oapp_module_contract.eval(f"OApp._getPeerOrRevert({test_eid})")


def test_setDelegate(oapp_module_contract, dev_deployer):
    """Test setDelegate function"""
    delegate = boa.env.generate_address()

    with boa.env.prank(dev_deployer):
        oapp_module_contract.setDelegate(delegate)
