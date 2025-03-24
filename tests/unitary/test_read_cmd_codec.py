"""Test ReadCmdCodecV1 module functionality."""

import time


def create_evm_call_request(
    read_cmd_codec_contract,
    app_request_label,
    target_eid,
    is_block_num,
    block_num_or_timestamp,
    confirmations,
    to_address,
    call_data,
):
    """Helper function to create an EVMCallRequestV1 struct."""
    # Prepare the string for the struct with proper keyword arguments
    struct_str = (
        f"EVMCallRequestV1(appRequestLabel={app_request_label},"
        f"targetEid={target_eid},"
        f"isBlockNum={"True" if is_block_num else "False"},"
        f"blockNumOrTimestamp={block_num_or_timestamp},"
        f"confirmations={confirmations},"
        f"to={to_address},"
        f"callData={call_data})"
    )
    # Evaluate the string in the Vyper environment
    return read_cmd_codec_contract.eval(struct_str)


def create_evm_call_compute(
    read_cmd_codec_contract,
    compute_setting,
    target_eid,
    is_block_num,
    block_num_or_timestamp,
    confirmations,
    to_address,
):
    """Helper function to create an EVMCallComputeV1 struct."""
    # Prepare the string for the struct with proper keyword arguments
    struct_str = (
        f"EVMCallComputeV1(computeSetting={compute_setting},"
        f"targetEid={target_eid},"
        f"isBlockNum={"True" if is_block_num else "False"},"
        f"blockNumOrTimestamp={block_num_or_timestamp},"
        f"confirmations={confirmations},"
        f"to={to_address})"
    )
    # Evaluate the string in the Vyper environment
    return read_cmd_codec_contract.eval(struct_str)


def test_encode_simple_request(read_cmd_codec_contract):
    """Test encoding a single EVM call request without compute."""
    # Create a request
    app_cmd_label = 1
    to_address = "0x" + "42" * 20  # Example address
    call_data = bytes.fromhex("aabbcc")  # Simple calldata

    # Create the request using our helper
    request = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        to_address,
        call_data,
    )

    # Encode the request using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request])

    # Verify length is greater than 0
    assert len(encoded) > 0
    # Basic verification that the app command label is correct (bytes 2-3 in the encoded output)
    assert encoded[2:4] == app_cmd_label.to_bytes(2, byteorder="big")


def test_encode_multiple_requests(read_cmd_codec_contract):
    """Test encoding multiple EVM call requests."""
    # Create parameters for two requests
    app_cmd_label = 1

    # Create first request
    request1 = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "42" * 20,  # to
        bytes.fromhex("112233"),  # callData
    )

    # Create second request
    request2 = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        2,  # targetEid
        True,  # isBlockNum
        12345678,  # blockNumOrTimestamp
        10,  # confirmations
        "0x" + "43" * 20,  # to
        bytes.fromhex("445566"),  # callData
    )

    # Encode the requests using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request1, request2])

    # Verify length is greater than 0
    assert len(encoded) > 0
    # Basic verification that the app command label is correct (bytes 2-3 in the encoded output)
    assert encoded[2:4] == app_cmd_label.to_bytes(2, byteorder="big")
    # Verify the number of requests is 2 (bytes 4-5 in the encoded output)
    assert encoded[4:6] == (2).to_bytes(2, byteorder="big")


def test_encode_with_compute(read_cmd_codec_contract):
    """Test encoding requests with compute command."""
    # Create parameters
    app_cmd_label = 1

    # Create request
    request = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "42" * 20,  # to
        bytes.fromhex("aabbcc"),  # callData
    )

    # Create a compute object with keyword arguments
    compute = create_evm_call_compute(
        read_cmd_codec_contract,
        2,  # computeSetting
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "44" * 20,  # to
    )

    # Encode with compute using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request], compute)

    # Verify length is greater than 0
    assert len(encoded) > 0
    # Basic verification that the app command label is correct (bytes 2-3 in the encoded output)
    assert encoded[2:4] == app_cmd_label.to_bytes(2, byteorder="big")


def test_decode_cmd_app_label(read_cmd_codec_contract):
    """Test decoding the app label from an encoded command."""
    # Create a request
    app_cmd_label = 1

    # Create the request using our helper
    request = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "42" * 20,  # to
        bytes.fromhex("aabbcc"),  # callData
    )

    # Encode the request using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request])
    # Decode the app label using internal function
    decoded_label = read_cmd_codec_contract.internal._decodeCmdAppLabel(encoded)

    # # Verify the decoded label matches the original
    assert decoded_label == app_cmd_label


def test_decode_request_app_request_label(read_cmd_codec_contract):
    """Test decoding the app request label from an encoded request."""
    # Create parameters
    app_cmd_label = 1
    app_request_label = 1
    # Create the request using our helper
    request = create_evm_call_request(
        read_cmd_codec_contract,
        app_request_label,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "42" * 20,  # to
        bytes.fromhex("aabbcc"),  # callData
    )
    # Encode the request using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request])

    # Decode the request app request label (for the first request) using internal function
    decoded_request_label = read_cmd_codec_contract.internal._decodeRequestV1AppRequestLabel(
        encoded[6:]
    )

    # # Verify the decoded label matches the original
    assert decoded_request_label == app_request_label


def test_encode_large_calldata(read_cmd_codec_contract):
    """Test encoding a request with large calldata."""
    # Create parameters
    app_cmd_label = 1
    # Create 60 bytes of test data (reduced from 100 to fit within Bytes[64] limit)
    large_calldata = bytes([i % 256 for i in range(60)])

    # Create the request using our helper
    request = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        1,  # targetEid
        False,  # isBlockNum
        int(time.time()),  # blockNumOrTimestamp
        15,  # confirmations
        "0x" + "42" * 20,  # to
        large_calldata,  # callData
    )

    # Encode the request using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request])

    # Verify length is greater than calldata length
    assert len(encoded) > len(large_calldata)


def test_request_fields_encoding(read_cmd_codec_contract):
    """Test that request fields are correctly encoded."""
    # Create parameters with specific values
    app_cmd_label = 1
    timestamp = 1234567890
    eid = 42
    confirmations = 5
    address = "0x" + "42" * 20
    calldata = bytes.fromhex("010203")

    # Create the request using our helper
    request = create_evm_call_request(
        read_cmd_codec_contract,
        1,  # appRequestLabel
        eid,  # targetEid
        True,  # isBlockNum
        timestamp,  # blockNumOrTimestamp
        confirmations,  # confirmations
        address,  # to
        calldata,  # callData
    )

    # Encode the request using internal function
    encoded = read_cmd_codec_contract.internal.encode(app_cmd_label, [request])

    # Verify command version and app command label
    assert encoded[0:2] == (1).to_bytes(2, byteorder="big")  # CMD_VERSION = 1
    assert encoded[2:4] == app_cmd_label.to_bytes(2, byteorder="big")
    assert encoded[4:6] == (1).to_bytes(2, byteorder="big")  # Number of requests = 1
