import time


class ExecutorOptions:
    """Helper for building LayerZero executor options"""

    # Constants from the contract
    WORKER_ID = 1
    TYPE_3 = bytes([0x00, 0x03])

    # Option types
    OPTION_TYPE_LZRECEIVE = 1
    OPTION_TYPE_NATIVE_DROP = 2
    OPTION_TYPE_LZCOMPOSE = 3
    OPTION_TYPE_ORDERED_EXECUTION = 4
    OPTION_TYPE_LZREAD = 5

    @staticmethod
    def new_options() -> bytes:
        """Start new type 3 options"""
        return ExecutorOptions.TYPE_3

    @staticmethod
    def add_executor_option(options: bytes, option_type: int, option_data: bytes) -> bytes:
        """Add an executor option to existing options"""
        return (
            options
            + bytes([ExecutorOptions.WORKER_ID])  # worker id
            + len(option_data + bytes([option_type])).to_bytes(2, "big")  # size
            + bytes([option_type])  # option type
            + option_data  # option data
        )

    @staticmethod
    def encode_lz_receive(gas: int, value: int = 0) -> bytes:
        """
        Encode LZ receive option
        @param gas Gas limit for lzReceive
        @param value Optional native value
        """
        if value == 0:
            return gas.to_bytes(16, "big")  # 128 bits
        return gas.to_bytes(16, "big") + value.to_bytes(16, "big")

    @staticmethod
    def encode_lz_read(gas: int, data_size: int) -> bytes:
        """
        Encode LZ read option
        @param gas Gas limit for execution
        @param data_size Expected response data size
        """
        return gas.to_bytes(16, "big") + data_size.to_bytes(4, "big")

    @staticmethod
    def encode_native_drop(amount: int, receiver: bytes) -> bytes:
        """
        Encode native drop option
        @param amount Amount of native tokens
        @param receiver Receiver address as bytes32
        """
        assert len(receiver) == 32, "Receiver must be bytes32"
        return amount.to_bytes(16, "big") + receiver

    @staticmethod
    def encode_lz_compose(index: int, gas: int, value: int = 0) -> bytes:
        """
        Encode LZ compose option
        @param index Compose index
        @param gas Gas limit
        @param value Optional native value
        """
        if value == 0:
            return index.to_bytes(2, "big") + gas.to_bytes(16, "big")
        return index.to_bytes(2, "big") + gas.to_bytes(16, "big") + value.to_bytes(16, "big")

    @staticmethod
    def add_lz_receive_option(options: bytes, gas: int, value: int = 0) -> bytes:
        """Add LZ receive option to existing options"""
        option_data = ExecutorOptions.encode_lz_receive(gas, value)
        return ExecutorOptions.add_executor_option(
            options, ExecutorOptions.OPTION_TYPE_LZRECEIVE, option_data
        )

    @staticmethod
    def add_native_drop_option(options: bytes, amount: int, receiver: bytes) -> bytes:
        """Add native drop option to existing options"""
        option_data = ExecutorOptions.encode_native_drop(amount, receiver)
        return ExecutorOptions.add_executor_option(
            options, ExecutorOptions.OPTION_TYPE_NATIVE_DROP, option_data
        )

    @staticmethod
    def add_lz_read_option(options: bytes, gas: int, data_size: int) -> bytes:
        """Add LZ read option to existing options"""
        option_data = ExecutorOptions.encode_lz_read(gas, data_size)
        return ExecutorOptions.add_executor_option(
            options, ExecutorOptions.OPTION_TYPE_LZREAD, option_data
        )


class ReadCodec:
    """Helper for encoding read requests"""

    CMD_VERSION = 1
    REQUEST_VERSION = 1
    RESOLVER_TYPE = 1

    @staticmethod
    def encode_request(request) -> bytes:
        # Calculate size (fixed 35 bytes + calldata)
        request_size = len(request["callData"]) + 35

        # 1. Headers (13 bytes)
        headers = (
            ReadCodec.CMD_VERSION.to_bytes(2, "big")  # cmd version
            + (0).to_bytes(2, "big")  # appCmdLabel
            + (1).to_bytes(2, "big")  # requests length
            + ReadCodec.REQUEST_VERSION.to_bytes(1, "big")  # request version
            + request["appRequestLabel"].to_bytes(2, "big")  # request label
            + ReadCodec.RESOLVER_TYPE.to_bytes(2, "big")  # resolver type
            + request_size.to_bytes(2, "big")  # size of what follows
        )

        # 2. Request fields (35 bytes + calldata)
        fields = (
            request["targetEid"].to_bytes(4, "big")  # target eid
            + (1 if request["isBlockNum"] else 0).to_bytes(1, "big")  # isBlockNum
            + request["blockNumOrTimestamp"].to_bytes(8, "big")  # block/time
            + request["confirmations"].to_bytes(2, "big")  # confirmations
            + bytes.fromhex(request["to"][2:])  # target address
            + request["callData"]  # calldata
        )

        return headers + fields


def build_default_options(gas: int = 60000) -> bytes:
    """Build default options with LZ receive gas"""
    options = ExecutorOptions.new_options()  # type 3
    return ExecutorOptions.add_lz_receive_option(options, gas)


def test_executor_options():
    # Check vanilla 60k gas option matches docs
    options = build_default_options(60000)
    assert (
        options.hex() == "0003010011010000000000000000000000000000ea60"
    )  # hardcoded value from LZ docs

    print(f"Default options: 0x{options.hex()}")

    # Test with different gas
    options_100k = build_default_options(100000)
    print(f"100k gas options: 0x{options_100k.hex()}")

    # Test multiple options
    options = ExecutorOptions.new_options()
    options = ExecutorOptions.add_lz_receive_option(options, 60000)
    options = ExecutorOptions.add_native_drop_option(
        options, amount=1000000, receiver=bytes.fromhex("00" * 32)
    )
    print(f"Options with native drop: 0x{options.hex()}")


def test_contract_options(lz_module_contract):
    # Test contract options
    options_python = build_default_options(60000)
    print(f"Python options: 0x{options_python.hex()}")
    options_contract = lz_module_contract.eval(f"self._prepare_message_options({60000})")
    print(f"Contract options: 0x{options_contract.hex()}")
    assert options_python == options_contract


def test_lz_read_options():
    """Test LZ Read option building"""
    # Test basic read option
    options = ExecutorOptions.new_options()
    options = ExecutorOptions.add_lz_read_option(options, gas=100000, data_size=64)
    print("\nLZ Read options (100k gas, 64 bytes):")
    print(f"0x{options.hex()}")


# Compare with contract
def test_contract_read_options(lz_module_contract):
    options_python = ExecutorOptions.new_options()
    options_python = ExecutorOptions.add_lz_read_option(options_python, gas=100000, data_size=64)
    options_contract = lz_module_contract.eval(f"self._prepare_read_options({100000}, {64})")
    print(f"\nPython read options: 0x{options_python.hex()}")
    print(f"Contract read options: 0x{options_contract.hex()}")
    assert options_python == options_contract


def test_read_request_encoding():
    """Test read request encoding"""
    # Create sample request
    request_dict = {
        "appRequestLabel": 1,
        "targetEid": 1,  # example chain id
        "isBlockNum": False,
        "blockNumOrTimestamp": int(time.time()),
        "confirmations": 15,
        "to": "0x" + "42" * 20,  # example address
        "callData": bytes.fromhex("aabbcc"),  # example calldata
    }

    encoded = ReadCodec.encode_request(request_dict)
    print("\nEncoded read request:")
    print(f"0x{encoded.hex()}")


# Compare with contract
def test_contract_request_encoding(lz_module_contract):
    # Create same request in contract format
    request_dict = {
        "appRequestLabel": 1,
        "targetEid": 1,  # example chain id
        "isBlockNum": False,
        "blockNumOrTimestamp": int(time.time()),
        "confirmations": 15,
        "to": "0x" + "42" * 20,  # example address
        "callData": bytes.fromhex("aabbcc"),  # example calldata
    }
    encoded_python = ReadCodec.encode_request(request_dict)
    kwargs = []
    for k, v in request_dict.items():
        if k == "to":
            # Remove quotes for address
            kwargs.append(f"{k}={v}")  # v already has 0x prefix
        else:
            kwargs.append(f"{k}={repr(v)}")
    kwargs_str = ", ".join(kwargs)
    argument = f"EVMCallRequestV1({kwargs_str})"
    encoded_contract = lz_module_contract.eval(f"self._encode_read_request({argument})")

    print(f"\nPython encoded request: 0x{encoded_python.hex()}")
    print(f"Contract encoded request: 0x{encoded_contract.hex()}")
    assert encoded_python == encoded_contract
