# @version ~=0.4

"""
@title Layer Zero V2 Vyper Module

@notice Base contract for LayerZero cross-chain messaging. Provides core
functionality for sending and receiving messages across chains.

@dev
- Handles message sending with proper fee management and security checks.
- Uses internal functions for core logic that can be called by importing contract.
- Example lzReceive implementation to be overridden by importing contract.
- Storage includes peers mapping and default gas settings.
- Functions:
  - _send_message: Internal, sends message to destination chain
  - _quote_lz_fee: Internal, quotes fees for message sending
  - _lz_receive: Internal base implementation of lzReceive with security checks

@custom:security Always verify peers and endpoints for cross-chain security
"""


################################################################
#                           CONSTANTS                          #
################################################################


# Because vyper does not support dynamic bytes arrays, we need to define a maximum size
# for the message payload. This shouldn't be set too high (like >10k) to avoid excessive gas costs.
LZ_MESSAGE_SIZE_CAP: public(constant(uint256)) = 512
LZ_READ_CALLDATA_SIZE: public(
    constant(uint256)
) = 256  # Max size for call data in read requests, must be lower than LZ_MESSAGE_SIZE_CAP

# LayerZero specific constants
TYPE_3: constant(bytes2) = 0x0003
WORKER_ID: constant(bytes1) = 0x01
OPTION_TYPE_LZRECEIVE: constant(bytes1) = 0x01
OPTION_TYPE_LZREAD: constant(bytes1) = 0x05

# Read channel related
READ_CHANNEL: constant(uint32) = 4294967294  # max(uint32)-1
READ_CHANNEL_THRESHOLD: constant(uint32) = 4294965694  # max(uint32)-1600

# Read codec constants
CMD_VERSION: constant(uint16) = 1
REQUEST_VERSION: constant(uint8) = 1
RESOLVER_TYPE: constant(uint16) = 1  # RESOLVER_TYPE_SINGLE_VIEW_EVM_CALL


################################################################
#                           STRUCTS                            #
################################################################


struct MessagingParams:
    dstEid: uint32
    receiver: bytes32  # Low level format for LZ
    message: Bytes[LZ_MESSAGE_SIZE_CAP]
    options: Bytes[64]
    payInLzToken: bool


struct MessagingFee:
    nativeFee: uint256
    lzTokenFee: uint256


struct Origin:
    srcEid: uint32
    sender: bytes32
    nonce: uint64


# LZ Read specific struct
struct EVMCallRequestV1:
    appRequestLabel: uint16
    targetEid: uint32
    isBlockNum: bool
    blockNumOrTimestamp: uint64
    confirmations: uint16
    to: address
    callData: Bytes[LZ_READ_CALLDATA_SIZE]


################################################################
#                         INTERFACES                           #
################################################################


interface ILayerZeroEndpointV2:
    def quote(_params: MessagingParams, _sender: address) -> MessagingFee: view

    def send(_params: MessagingParams, _refundAddress: address) -> (
        bytes32, uint64, uint256, uint256
    ): payable


################################################################
#                           STORAGE                            #
################################################################


LZ_ENDPOINT: public(immutable(address))  # LayerZero endpoint address on deployed chain
LZ_PEERS: public(HashMap[uint32, address])  # Chain ID => Trusted peer address
default_gas_limit: public(uint256)  # Default gas limit for cross-chain messages


################################################################
#                         CONSTRUCTOR                          #
################################################################


@deploy
def __init__(_endpoint: address, _gas_limit: uint256):
    """
    @notice Initialize the LayerZero base module
    @param _endpoint The LZ endpoint address
    @param _gas_limit Default gas limit for cross-chain messages
    """
    LZ_ENDPOINT = _endpoint
    self.default_gas_limit = _gas_limit


################################################################
#                      INTERNAL FUNCTIONS                      #
################################################################


@internal
def _set_default_gas_limit(_gas_limit: uint256):
    """
    @notice Update default gas limit for messages
    @dev Must be guarded by owner check in importing contract
    """
    self.default_gas_limit = _gas_limit


@internal
def _set_peer(_srcEid: uint32, _peer: address):
    """
    @notice Set trusted peer for given chain ID
    @dev Must be guarded by owner check in importing contract
    """
    self.LZ_PEERS[_srcEid] = _peer


@internal
@pure
def _build_lz_receive_option(_gas: uint256) -> Bytes[32]:
    """
    @notice Build LayerZero options with specified gas limit
    @param _gas Gas limit for execution
    """
    return concat(
        TYPE_3,
        WORKER_ID,
        convert(17, bytes2),
        OPTION_TYPE_LZRECEIVE,
        convert(convert(_gas, uint128), bytes16),
    )


@internal
@pure
def _build_lz_read_option(
    _gas: uint256,
    _data_size: uint32,
) -> Bytes[32]:
    """
    @notice Build LayerZero read options
    @param _gas Gas limit for execution
    @param _data_size Expected response data size
    """
    return concat(
        TYPE_3,
        WORKER_ID,
        convert(21, bytes2),  # length (16 + 4 + 1)
        OPTION_TYPE_LZREAD,
        convert(convert(_gas, uint128), bytes16),  # gas
        convert(_data_size, bytes4),  # data size
    )


@internal
@pure
def _encode_read_request(_request: EVMCallRequestV1) -> Bytes[LZ_MESSAGE_SIZE_CAP]:
    """
    @notice Encode read request following ReadCmdCodecV1 format
    @param _request The read request to encode
    """
    # Get total request size (calldata + fixed fields = 35 bytes)
    request_size: uint16 = convert(len(_request.callData) + 35, uint16)

    # 1. Start with headers
    encoded_headers: Bytes[13] = concat(
        convert(CMD_VERSION, bytes2),  # cmd version = 1
        convert(0, bytes2),  # appCmdLabel = 0
        convert(1, bytes2),  # requests length = 1
        convert(REQUEST_VERSION, bytes1),  # request version = 1
        convert(_request.appRequestLabel, bytes2),  # request label
        convert(RESOLVER_TYPE, bytes2),  # resolver type = 1
        convert(request_size, bytes2),  # size of what follows
    )

    # 2. Add request fields
    encoded: Bytes[LZ_MESSAGE_SIZE_CAP] = concat(
        encoded_headers,  # 13 bytes
        convert(_request.targetEid, bytes4),  # +4=17
        convert(_request.isBlockNum, bytes1),  # +1=18
        convert(_request.blockNumOrTimestamp, bytes8),  # +8=26
        convert(_request.confirmations, bytes2),  # +2=28
        convert(_request.to, bytes20),  # +20=48 (35 without headers)
        _request.callData,  # +LZ_READ_CALLDATA_SIZE
    )

    return encoded


@internal
@view
def _quote_lz_read_fee(
    _request: EVMCallRequestV1, _gas_limit: uint256 = 0, _data_size: uint32 = 64
) -> uint256:
    """
    @notice Get fee quote for read request
    @param _request The read request struct
    @param _gas_limit Optional gas limit (uses default if 0)
    @param _data_size Expected response size
    @return Required fee in native currency
    """
    gas: uint256 = _gas_limit if _gas_limit != 0 else self.default_gas_limit
    options: Bytes[64] = self._build_lz_read_option(gas, _data_size)
    read_cmd: Bytes[LZ_MESSAGE_SIZE_CAP] = self._encode_read_request(_request)

    params: MessagingParams = MessagingParams(
        dstEid=READ_CHANNEL,
        receiver=empty(bytes32),
        message=read_cmd,
        options=options,
        payInLzToken=False,
    )
    fees: MessagingFee = staticcall ILayerZeroEndpointV2(LZ_ENDPOINT).quote(params, self)
    return fees.nativeFee


@internal
@view
def _quote_lz_fee(
    _dstEid: uint32,
    _receiver: address,
    _message: Bytes[LZ_MESSAGE_SIZE_CAP],
    _gas_limit: uint256 = 0,
) -> uint256:
    """
    @notice Get fee quote for sending message
    @param _dstEid Destination chain ID
    @param _receiver Receiver address on destination
    @param _message Message payload
    @param _gas_limit Optional gas limit (uses default if 0)
    @return Required fee in native currency
    """
    gas: uint256 = _gas_limit if _gas_limit != 0 else self.default_gas_limit
    options: Bytes[64] = self._build_lz_receive_option(gas)

    params: MessagingParams = MessagingParams(
        dstEid=_dstEid,
        receiver=convert(convert(_receiver, bytes20), bytes32),
        message=_message,
        options=options,
        payInLzToken=False,
    )
    fees: MessagingFee = staticcall ILayerZeroEndpointV2(LZ_ENDPOINT).quote(params, self)
    return fees.nativeFee


@payable
@internal
def _send_message(
    _dstEid: uint32,
    _receiver: address,
    _message: Bytes[LZ_MESSAGE_SIZE_CAP],
    _gas_limit: uint256 = 0,
    _skip_fee_check: bool = False,
):
    """
    @notice Send message through LayerZero
    @param _dstEid Destination chain ID
    @param _receiver Receiver address on destination
    @param _message Message payload
    @param _gas_limit Optional gas limit (uses default if 0)
    """
    gas: uint256 = _gas_limit if _gas_limit != 0 else self.default_gas_limit
    options: Bytes[64] = self._build_lz_receive_option(gas)

    params: MessagingParams = MessagingParams(
        dstEid=_dstEid,
        receiver=convert(_receiver, bytes32),
        message=_message,
        options=options,
        payInLzToken=False,
    )

    if not _skip_fee_check:
        fees: MessagingFee = staticcall ILayerZeroEndpointV2(LZ_ENDPOINT).quote(params, self)
        assert msg.value >= fees.nativeFee, "Not enough fees"

    extcall ILayerZeroEndpointV2(LZ_ENDPOINT).send(params, msg.sender, value=msg.value)


@payable
@internal
def _lz_receive(
    _origin: Origin,
    _guid: bytes32,
    _message: Bytes[LZ_MESSAGE_SIZE_CAP],
    _executor: address,
    _extraData: Bytes[64],
) -> bool:
    """
    @notice Base lzReceive with security checks
    @dev Must be called by importing contract's lzReceive implementation
    """
    assert msg.sender == LZ_ENDPOINT, "Not LZ endpoint"
    assert self.LZ_PEERS[_origin.srcEid] != empty(address), "Peer not set"
    assert convert(_origin.sender, address) == self.LZ_PEERS[_origin.srcEid], "Invalid peer"
    return True



@payable
@internal
def _send_read_request(
    _request: EVMCallRequestV1,
    _gas_limit: uint256 = 0,
    _data_size: uint32 = 64,
    _skip_fee_check: bool = False,
):
    """
    @notice Send read request through LayerZero
    @param _request The read request struct
    @param _gas_limit Optional gas limit
    @param _data_size Expected response size
    @param _skip_fee_check Skip fee amount verification
    """
    gas: uint256 = _gas_limit if _gas_limit != 0 else self.default_gas_limit
    options: Bytes[64] = self._build_lz_read_option(gas, _data_size)
    read_cmd: Bytes[LZ_MESSAGE_SIZE_CAP] = self._encode_read_request(_request)

    params: MessagingParams = MessagingParams(
        dstEid=READ_CHANNEL,
        receiver=empty(bytes32),
        message=read_cmd,
        options=options,
        payInLzToken=False,
    )

    if not _skip_fee_check:
        fees: MessagingFee = staticcall ILayerZeroEndpointV2(LZ_ENDPOINT).quote(params, self)
        assert msg.value >= fees.nativeFee, "Not enough fees"

    extcall ILayerZeroEndpointV2(LZ_ENDPOINT).send(params, msg.sender, value=msg.value)


################################################################
#                     EXPORTED FUNCTIONS                       #
################################################################


@view
@external
def quote_lz_fee(
    _dstEid: uint32,
    _receiver: address,
    _message: Bytes[LZ_MESSAGE_SIZE_CAP],
    _gas_limit: uint256 = 0,
) -> uint256:
    """
    @notice External fee quote for testing
    @return Required fee in native currency
    """
    return self._quote_lz_fee(_dstEid, _receiver, _message, _gas_limit)


@view
@external
def quote_lz_read_fee(
    _request: EVMCallRequestV1, _gas_limit: uint256 = 0, _data_size: uint32 = 64
) -> uint256:
    """
    @notice External fee quote for read request
    @return Required fee in native currency
    """
    return self._quote_lz_read_fee(_request, _gas_limit, _data_size)


################################################################
#                        LZ ENDPOINTS                          #
################################################################

@view
@external
def nextNonce(_srcEid: uint32, _sender: bytes32) -> uint64:
    """
    @notice Dummy endpoint for protocol needs
    @dev Returns 0, but can be used to track nonces
    """
    return 0


@view
@external
def allowInitializePath(_origin: Origin) -> bool:
    """
    @notice Dummy endpoint for protocol needs
    @dev Returns True, but can be used to verify sender
    """
    return True
