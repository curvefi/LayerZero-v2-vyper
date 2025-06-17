"""Test OptionsBuilder module functionality."""

from binascii import hexlify
from conftest import _to_bytes32
import boa


def test_new_options(options_builder_contract):
    """Test creating new options with type 3."""
    options = options_builder_contract.internal.newOptions()

    # Options should start with type 3 (0x0003)
    assert hexlify(options[:2]).decode() == "0003"
    assert len(options) == 2, "Initial options should only contain type (2 bytes)"


def test_add_executor_lz_receive_option(options_builder_contract):
    """Test adding an executor LZ receive option."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add LZ receive option with gas limit only
    gas_limit = 60_000
    options = options_builder_contract.internal.addExecutorLzReceiveOption(options, gas_limit, 0)

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0011) + OPTION_TYPE(0x01) + GAS_LIMIT(16 bytes)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert (
        int.from_bytes(options[3:5], "big") == 17
    ), "Option size should be 17 bytes (1 for type + 16 for gas)"
    assert options[5] == 1, "Option type should be 1 (LZ receive)"

    # Extract gas limit (big-endian 16 bytes)
    option_gas = int.from_bytes(options[6:22], "big")
    assert option_gas == gas_limit, "Gas limit should match the input value"


def test_add_executor_lz_receive_option_with_value(options_builder_contract):
    """Test adding an executor LZ receive option with value."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add LZ receive option with gas limit and value
    gas_limit = 60_000
    value = 1_000_000  # 1M wei
    options = options_builder_contract.internal.addExecutorLzReceiveOption(
        options, gas_limit, value
    )

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0021) + OPTION_TYPE(0x01) + GAS_LIMIT(16 bytes) + VALUE(16 bytes)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 33, "Option size should be 33 bytes (1 + 16 + 16)"
    assert options[5] == 1, "Option type should be 1 (LZ receive)"

    # Extract gas limit and value (big-endian 16 bytes each)
    option_gas = int.from_bytes(options[6:22], "big")
    option_value = int.from_bytes(options[22:38], "big")
    assert option_gas == gas_limit, "Gas limit should match the input value"
    assert option_value == value, "Value should match the input value"


def test_add_executor_native_drop_option(options_builder_contract):
    """Test adding an executor native drop option."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add native drop option
    amount = 1_000_000  # 1M wei
    recipient = "0x" + "42" * 20  # Example address

    # Pass the bytes32 recipient properly formatted
    options = options_builder_contract.internal.addExecutorNativeDropOption(
        options, amount, _to_bytes32(recipient)
    )

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0031) + OPTION_TYPE(0x02) + AMOUNT(16 bytes) + RECIPIENT(32 bytes)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 49, "Option size should be 49 bytes (1 + 16 + 32)"
    assert options[5] == 2, "Option type should be 2 (native drop)"

    # Extract amount (big-endian 16 bytes)
    option_amount = int.from_bytes(options[6:22], "big")
    assert option_amount == amount, "Amount should match the input value"


def test_add_executor_lz_compose_option(options_builder_contract):
    """Test adding an executor LZ compose option."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add LZ compose option
    index = 1
    gas_limit = 60_000
    options = options_builder_contract.internal.addExecutorLzComposeOption(
        options, index, gas_limit, 0
    )

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0013) + OPTION_TYPE(0x03) + INDEX(2 bytes) + GAS_LIMIT(16 bytes)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 19, "Option size should be 19 bytes (1 + 2 + 16)"
    assert options[5] == 3, "Option type should be 3 (LZ compose)"

    # Extract index and gas limit
    option_index = int.from_bytes(options[6:8], "big")
    option_gas = int.from_bytes(options[8:24], "big")
    assert option_index == index, "Index should match the input value"
    assert option_gas == gas_limit, "Gas limit should match the input value"


def test_add_executor_ordered_execution_option(options_builder_contract):
    """Test adding an executor ordered execution option."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add ordered execution option
    options = options_builder_contract.internal.addExecutorOrderedExecutionOption(options)

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0001) + OPTION_TYPE(0x04)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 1, "Option size should be 1 byte (type only)"
    assert options[5] == 4, "Option type should be 4 (ordered execution)"


def test_add_executor_lz_read_option(options_builder_contract):
    """Test adding an executor LZ read option."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add LZ read option
    gas_limit = 60_000
    expected_response_size = 64
    options = options_builder_contract.internal.addExecutorLzReadOption(
        options, gas_limit, expected_response_size, 0
    )

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0015) + OPTION_TYPE(0x05) + GAS_LIMIT(16 bytes) + RESPONSE_SIZE(4 bytes)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 21, "Option size should be 21 bytes (1 + 16 + 4)"
    assert options[5] == 5, "Option type should be 5 (LZ read)"

    # Extract gas limit and response size
    option_gas = int.from_bytes(options[6:22], "big")
    option_size = int.from_bytes(options[22:26], "big")
    assert option_gas == gas_limit, "Gas limit should match the input value"
    assert option_size == expected_response_size, "Response size should match the input value"


def test_add_executor_lz_read_option_with_value(options_builder_contract):
    """Test adding an executor LZ read option with value."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add LZ read option with value
    gas_limit = 60_000
    expected_response_size = 64
    value = 1_000_000  # 1M wei
    options = options_builder_contract.internal.addExecutorLzReadOption(
        options, gas_limit, expected_response_size, value
    )

    # Inspect the options
    # Format: TYPE(0x0003) + WORKER_ID(0x01) + SIZE(0x0025) + OPTION_TYPE(0x05) + GAS_LIMIT(16) + RESPONSE_SIZE(4) + VALUE(16)
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"
    assert options[2] == 1, "Executor worker ID should be 1"
    assert (
        int.from_bytes(options[3:5], "big") == 37
    ), "Option size should be 37 bytes (1 + 16 + 4 + 16)"
    assert options[5] == 5, "Option type should be 5 (LZ read)"

    # Extract gas limit, response size, and value
    option_gas = int.from_bytes(options[6:22], "big")
    option_size = int.from_bytes(options[22:26], "big")
    option_value = int.from_bytes(options[26:42], "big")
    assert option_gas == gas_limit, "Gas limit should match the input value"
    assert option_size == expected_response_size, "Response size should match the input value"
    assert option_value == value, "Value should match the input value"


def test_multiple_options(options_builder_contract):
    """Test adding multiple options to the same options container."""
    # Create new options
    options = options_builder_contract.internal.newOptions()

    # Add multiple options
    gas_limit = 60_000
    options = options_builder_contract.internal.addExecutorLzReceiveOption(options, gas_limit, 0)
    options = options_builder_contract.internal.addExecutorOrderedExecutionOption(options)

    # Check that the options are correctly formatted
    assert hexlify(options[:2]).decode() == "0003", "Options should start with type 3"

    # First option bytes 2-5
    assert options[2] == 1, "First option worker ID should be 1"
    assert int.from_bytes(options[3:5], "big") == 17, "First option size should be 17 bytes"
    assert options[5] == 1, "First option type should be 1 (LZ receive)"

    # Second option should start at byte 22 (2 + 3 + 17)
    assert options[22] == 1, "Second option worker ID should be 1"
    assert int.from_bytes(options[23:25], "big") == 1, "Second option size should be 1 byte"
    assert options[25] == 4, "Second option type should be 4 (ordered execution)"


def test_executor_option_size_limit_enforcement(options_builder_contract, constants):
    """Test executor options respect size limits with proper sanity check"""
    # Get constants
    max_size = constants._constants.MAX_OPTIONS_TOTAL_SIZE
    max_single = constants._constants.MAX_OPTION_SINGLE_SIZE

    # Start with new options
    options = options_builder_contract.internal.newOptions()

    option_size = 36
    assert len(options) == 2  # must be TYPE_3 only

    # Calculate max options that fit: (convert_limit - initial_size) // option_size
    max_options = (max_size - max_single - 4 - 2) // option_size  # 2 for initial, 36 per option
    max_options += max_single > option_size  # one more could fit, but then assert will fail
    # Add maximum options
    for i in range(max_options):
        options = options_builder_contract.internal.addExecutorLzReceiveOption(
            options, 100000 + i, 1000 + i
        )

    # Verify size: initial (2) + options (max_options * 36)
    assert len(options) == 2 + max_options * option_size
    print(f"Options: {len(options)}")
    # Next option should revert due to assert limit
    with boa.reverts():
        options_builder_contract.internal.addExecutorLzReceiveOption(
            options, 100000 + max_options, 1000 + max_options
        )
