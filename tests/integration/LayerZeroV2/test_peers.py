from eth_utils import to_checksum_address


def test_set_peer(lz_module_contract):
    """Test basic peer setting functionality"""
    # Set up test data
    test_eid = 1234
    test_peer = to_checksum_address("0x" + "42" * 20)

    # Initially should be empty
    assert lz_module_contract.LZ_PEERS(test_eid) == "0x" + "00" * 20
    assert len(lz_module_contract.get_configured_eids()) == 0

    # Set peer
    lz_module_contract.eval(f"self._set_peer({test_eid}, {test_peer})")

    # Verify peer is set
    assert lz_module_contract.LZ_PEERS(test_eid) == test_peer
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == 1
    assert configured_eids[0] == test_eid


def test_multiple_peers(lz_module_contract):
    """Test setting multiple peers"""
    # Set up test data
    peers = [
        (1234, to_checksum_address("0x" + "42" * 20)),
        (5678, to_checksum_address("0x" + "43" * 20)),
        (9012, to_checksum_address("0x" + "44" * 20)),
    ]

    # Set multiple peers
    for eid, peer in peers:
        lz_module_contract.eval(f"self._set_peer({eid}, {peer})")

    # Verify all peers are set
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == len(peers)

    for eid, peer in peers:
        assert lz_module_contract.LZ_PEERS(eid) == peer
        assert eid in configured_eids


def test_remove_peer(lz_module_contract):
    """Test removing peers"""
    # Set up initial peers
    test_eid_1 = 1234
    test_peer_1 = to_checksum_address("0x" + "42" * 20)
    test_eid_2 = 5678
    test_peer_2 = to_checksum_address("0x" + "43" * 20)

    # Add peers
    lz_module_contract.eval(f"self._set_peer({test_eid_1}, {test_peer_1})")
    lz_module_contract.eval(f"self._set_peer({test_eid_2}, {test_peer_2})")
    assert len(lz_module_contract.get_configured_eids()) == 2

    # Remove first peer by setting to zero address
    lz_module_contract.eval(f"self._set_peer({test_eid_1}, {'0x' + '00' * 20})")

    # Verify peer is removed
    assert lz_module_contract.LZ_PEERS(test_eid_1) == "0x" + "00" * 20
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == 1
    assert test_eid_1 not in configured_eids
    assert test_eid_2 in configured_eids


def test_update_peer(lz_module_contract):
    """Test updating existing peer"""
    test_eid = 1234
    test_peer_1 = to_checksum_address("0x" + "42" * 20)
    test_peer_2 = to_checksum_address("0x" + "43" * 20)

    # Set initial peer
    lz_module_contract.eval(f"self._set_peer({test_eid}, {test_peer_1})")
    assert lz_module_contract.LZ_PEERS(test_eid) == test_peer_1
    assert len(lz_module_contract.get_configured_eids()) == 1

    # Update to new peer
    lz_module_contract.eval(f"self._set_peer({test_eid}, {test_peer_2})")

    # Verify update
    assert lz_module_contract.LZ_PEERS(test_eid) == test_peer_2
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == 1
    assert test_eid in configured_eids


def test_peer_list_maintenance(lz_module_contract):
    """Test comprehensive peer list maintenance"""
    peers = [
        (1234, to_checksum_address("0x" + "42" * 20)),
        (5678, to_checksum_address("0x" + "43" * 20)),
        (9012, to_checksum_address("0x" + "44" * 20)),
    ]

    # Add all peers
    for eid, peer in peers:
        lz_module_contract.eval(f"self._set_peer({eid}, {peer})")
    assert len(lz_module_contract.get_configured_eids()) == 3

    # Remove middle peer
    lz_module_contract.eval(f"self._set_peer({peers[1][0]}, {'0x' + '00' * 20})")

    # Verify list is maintained correctly
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == 2
    assert peers[0][0] in configured_eids
    assert peers[1][0] not in configured_eids
    assert peers[2][0] in configured_eids

    # Add new peer
    new_eid = 1111
    new_peer = to_checksum_address("0x" + "45" * 20)
    lz_module_contract.eval(f"self._set_peer({new_eid}, {new_peer})")

    # Verify new peer is added correctly
    configured_eids = lz_module_contract.get_configured_eids()
    assert len(configured_eids) == 3
    assert new_eid in configured_eids
