"""Test OAppReceiver functionality for OApp."""

import boa
from conftest import _to_bytes32, LZ_ENDPOINT_BASE_SEPOLIA, LZ_ENDPOINT_ID


def test_is_compose_msg_sender(oapp_module_contract, dev_deployer):
    """Test isComposeMsgSender returns true for self, false otherwise."""
    # Set up test data
    origin = (
        LZ_ENDPOINT_ID,  # srcEid
        _to_bytes32(dev_deployer),  # sender
        1,  # nonce
    )
    test_message = bytes("Test message", "utf-8")

    # Test with the contract address as sender (should return true)
    result = oapp_module_contract.isComposeMsgSender(
        origin, test_message, oapp_module_contract.address
    )
    assert result is True

    # Test with a different address as sender (should return false)
    different_address = boa.env.generate_address()
    result = oapp_module_contract.isComposeMsgSender(origin, test_message, different_address)
    assert result is False


def test_allow_initialize_path_with_peer_set(oapp_module_contract, dev_deployer):
    """Test allowInitializePath returns true when peer is set."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(dev_deployer)

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Create origin struct with matching peer
    origin = (
        test_eid,  # srcEid
        test_peer,  # sender
        1,  # nonce
    )

    # Check if path initialization is allowed
    result = oapp_module_contract.allowInitializePath(origin)
    assert result is True

    # Test with different peer
    wrong_peer_origin = (
        test_eid,  # srcEid
        _to_bytes32(boa.env.generate_address()),  # different sender
        1,  # nonce
    )
    result = oapp_module_contract.allowInitializePath(wrong_peer_origin)
    assert result is False


def test_allow_initialize_path_with_no_peer(oapp_module_contract):
    """Test allowInitializePath returns false when no peer is set."""
    # Set up test data without setting a peer
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(boa.env.generate_address())

    # Create origin struct with non-matching peer
    origin = (
        test_eid,  # srcEid
        test_peer,  # sender
        1,  # nonce
    )

    # Check if path initialization is allowed (should be false)
    result = oapp_module_contract.allowInitializePath(origin)
    assert result is False


def test_next_nonce(oapp_module_contract):
    """Test nextNonce returns 0 by default (no nonce ordering)."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(boa.env.generate_address())

    # Check if nextNonce returns 0 (default)
    nonce = oapp_module_contract.nextNonce(test_eid, test_peer)
    assert nonce == 0

    # Test with different values (should still return 0)
    nonce = oapp_module_contract.nextNonce(999, _to_bytes32("random"))
    assert nonce == 0


# Tests for the internal _lzReceive functionality
def test_lz_receive_basic(oapp_module_contract, dev_deployer):
    """Test basic _lzReceive functionality through eval."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(dev_deployer)
    test_message = bytes("Test message", "utf-8")

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Generate Origin struct outside lzReceive call
    origin_struct = f"OApp.Origin(srcEid={test_eid}, sender=convert({test_peer}, bytes32), nonce=1)"

    # Test _lzReceive with the endpoint as sender
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        eval_code = (
            f"OApp._lzReceive({origin_struct}, empty(bytes32), {test_message}, empty(address), b'')"
        )
        oapp_module_contract.eval(eval_code)

    # This doesn't revert, which means the function executed successfully


def test_lz_receive_invalid_sender(oapp_module_contract, dev_deployer):
    """Test _lzReceive reverts when caller is not endpoint."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(dev_deployer)
    test_message = bytes("Test message", "utf-8")

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, test_peer)

    # Generate Origin struct outside lzReceive call
    origin_struct = f"OApp.Origin(srcEid={test_eid}, sender=convert({test_peer}, bytes32), nonce=1)"

    # Test _lzReceive with an invalid sender
    with boa.env.prank(dev_deployer):  # Not the endpoint
        with boa.reverts("OApp: only endpoint"):
            eval_code = f"OApp._lzReceive({origin_struct}, empty(bytes32), {test_message}, empty(address), b'')"
            oapp_module_contract.eval(eval_code)


def test_lz_receive_invalid_peer(oapp_module_contract, dev_deployer):
    """Test _lzReceive reverts when origin.sender is not a valid peer."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    valid_peer = _to_bytes32(dev_deployer)
    invalid_peer = _to_bytes32(boa.env.generate_address())
    test_message = bytes("Test message", "utf-8")

    # Set peer as owner
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, valid_peer)

    # Generate Origin struct outside lzReceive call
    origin_struct = (
        f"OApp.Origin(srcEid={test_eid}, sender=convert({invalid_peer}, bytes32), nonce=1)"
    )

    # Test _lzReceive with an invalid peer
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        with boa.reverts("OApp: invalid sender"):
            eval_code = f"OApp._lzReceive({origin_struct}, empty(bytes32), {test_message}, empty(address), b'')"
            oapp_module_contract.eval(eval_code)


def test_lz_receive_no_peer_set(oapp_module_contract, dev_deployer):
    """Test _lzReceive reverts when no peer is set for the origin chain."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    test_peer = _to_bytes32(dev_deployer)
    test_message = bytes("Test message", "utf-8")

    # Don't set a peer for test_eid

    # Generate Origin struct outside lzReceive call
    origin_struct = f"OApp.Origin(srcEid={test_eid}, sender=convert({test_peer}, bytes32), nonce=1)"

    # Test _lzReceive with no peer set
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        with boa.reverts("OApp: no peer"):
            eval_code = f"OApp._lzReceive({origin_struct}, empty(bytes32), {test_message}, empty(address), b'')"
            oapp_module_contract.eval(eval_code)


def test_lz_receive_with_zero_peer(oapp_module_contract, dev_deployer):
    """Test _lzReceive reverts when peer is set to zero."""
    # Set up test data
    test_eid = LZ_ENDPOINT_ID
    zero_peer = _to_bytes32("0x" + "00" * 20)
    test_message = bytes("Test message", "utf-8")

    # Set peer to zero bytes32
    with boa.env.prank(dev_deployer):
        oapp_module_contract.setPeer(test_eid, zero_peer)

    # Generate Origin struct outside lzReceive call
    origin_struct = f"OApp.Origin(srcEid={test_eid}, sender=convert({zero_peer}, bytes32), nonce=1)"

    # Test _lzReceive with zero peer
    with boa.env.prank(LZ_ENDPOINT_BASE_SEPOLIA):
        with boa.reverts("OApp: no peer"):
            eval_code = f"OApp._lzReceive({origin_struct}, empty(bytes32), {test_message}, empty(address), b'')"
            oapp_module_contract.eval(eval_code)
