# pragma version 0.4.1

"""
@title OApp (LayerZero V2 OApp Standard)

@notice Vyper implementation of LayerZero OApp standard.
This contract implements the OApp interface for cross-chain messaging via LayerZero.
It combines the functionality of OAppCore, OAppSender, OAppReceiver, and OAppRead
into a single contract.

@dev Core functionality includes:
1. Peer management - setting and verifying trusted remote endpoints
2. Message sending - quoting fees and sending messages across chains
3. Message receiving - verifying and processing inbound messages
4. Read requests - cross-chain view calls
5. Configuration - setting up endpoint libraries and DVN configurations

@license Copyright (c) Curve.Fi, 2025 - all rights reserved

@author curve.fi

@custom:security security@curve.fi
"""

################################################################
#                            MODULES                           #
################################################################

# Import ownership management
from snekmate.auth import ownable

initializes: ownable
exports: (
    ownable.owner,
    ownable.transfer_ownership,
    ownable.renounce_ownership,
)

# OptionsBuilder module
import OptionsBuilder

################################################################
#                         INTERFACES                           #
################################################################

# Import ERC20 interface for lzToken fee payment
from ethereum.ercs import IERC20

# LayerZero EndpointV2 interface
interface ILayerZeroEndpointV2:
    def quote(_params: MessagingParams, _sender: address) -> MessagingFee: view
    def send(_params: MessagingParams, _refundAddress: address) -> MessagingReceipt: payable
    def setDelegate(_delegate: address): nonpayable
    def setSendLibrary(_oapp: address, _eid: uint32, _newLib: address): nonpayable
    def setReceiveLibrary(
        _oapp: address, _eid: uint32, _newLib: address, _gracePeriod: uint256
    ): nonpayable
    def setConfig(_oapp: address, _lib: address, _params: DynArray[SetConfigParam, 1]): nonpayable
    def eid() -> uint32: view
    def lzToken() -> address: view
    def skip(_oapp: address, _srcEid: uint32, _sender: bytes32, _nonce: uint64): nonpayable


################################################################
#                           EVENTS                            #
################################################################

event PeerSet:
    eid: uint32
    peer: bytes32


# event MessageSent:
#     dstEid: uint32
#     message: Bytes[MAX_MESSAGE_SIZE]
#     nativeFee: uint256
#     lzTokenFee: uint256


# event MessageReceived:
#     srcEid: uint32
#     sender: bytes32
#     nonce: uint64
#     message: Bytes[MAX_MESSAGE_SIZE]


# event ReadRequest:
#     dstEid: uint32
#     to: address
#     callData: Bytes[MAX_READ_CALLDATA_SIZE]


# event ReadResponse:
#     srcEid: uint32
#     response: Bytes[MAX_MESSAGE_SIZE]


################################################################
#                           CONSTANTS                          #
################################################################

# Message size limits
MAX_MESSAGE_SIZE: public(constant(uint256)) = 512
MAX_EXTRA_DATA_SIZE: public(constant(uint256)) = 64

# # Options size limits
# MAX_OPTIONS_TOTAL_SIZE: public(constant(uint256)) = 256
# MAX_OPTION_SINGLE_SIZE: public(constant(uint256)) = 64

# # LayerZero protocol constants
# TYPE_1: constant(uint16) = 1
# TYPE_2: constant(uint16) = 2
# TYPE_3: constant(uint16) = 3

# EXECUTOR_WORKER_ID: constant(uint8) = 1
# DVN_WORKER_ID: constant(uint8) = 2

# # Option types
# OPTION_TYPE_LZRECEIVE: constant(uint8) = 1
# OPTION_TYPE_NATIVE_DROP: constant(uint8) = 2
# OPTION_TYPE_LZCOMPOSE: constant(uint8) = 3
# OPTION_TYPE_ORDERED_EXECUTION: constant(uint8) = 4
# OPTION_TYPE_LZREAD: constant(uint8) = 5

# # DVN option types
# OPTION_TYPE_DVN: constant(uint8) = 10
# OPTION_TYPE_DVN_PRECRIME: constant(uint8) = 1

# # Read codec constants
# CMD_VERSION: constant(uint16) = 1
# REQUEST_VERSION: constant(uint8) = 1
# RESOLVER_TYPE_SINGLE_VIEW_EVM_CALL: constant(uint16) = 1

# # Compute settings
# COMPUTE_SETTING_MAP_ONLY: constant(uint8) = 0
# COMPUTE_SETTING_REDUCE_ONLY: constant(uint8) = 1
# COMPUTE_SETTING_MAP_REDUCE: constant(uint8) = 2
# COMPUTE_SETTING_NONE: constant(uint8) = 3

# # Read channel threshold
# READ_CHANNEL_THRESHOLD: constant(
#     uint32
# ) = 4294965694  # max(uint32)-1601, 1600 channels reserved for read

# # Misc constants
# MAX_DVNS: constant(uint8) = 10
# MAX_PEERS: constant(uint256) = 128
# MAX_READ_REQUESTS: constant(uint256) = 16

# Core contract state (immutable)
ENDPOINT: public(immutable(ILayerZeroEndpointV2))

################################################################
#                           STORAGE                            #
################################################################

# Remote peers by EID
peers: public(HashMap[uint32, bytes32])

# # Ordered execution tracking (optional)
# ordered_nonce: public(bool)
# max_received_nonce: public(HashMap[uint32, HashMap[bytes32, uint64]])

################################################################
#                           STRUCTS                            #
################################################################

struct MessagingParams:
    dstEid: uint32
    receiver: bytes32
    message: Bytes[MAX_MESSAGE_SIZE]
    options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE]
    payInLzToken: bool


struct MessagingReceipt:
    guid: bytes32
    nonce: uint64
    fee: MessagingFee


struct MessagingFee:
    nativeFee: uint256
    lzTokenFee: uint256


struct Origin:
    srcEid: uint32
    sender: bytes32
    nonce: uint64


# struct EVMCallRequestV1:
#     appRequestLabel: uint16
#     targetEid: uint32
#     isBlockNum: bool
#     blockNumOrTimestamp: uint64
#     confirmations: uint16
#     to: address
#     callData: Bytes[MAX_READ_CALLDATA_SIZE]


# # Not using compute for now
# struct EVMCallComputeV1:
#     dummy: uint8  # Just to have something in the struct


struct SetConfigParam:
    eid: uint32
    configType: uint32
    config: Bytes[1024]


# struct ULNConfig:
#     confirmations: uint64
#     required_dvn_count: uint8
#     optional_dvn_count: uint8
#     optional_dvn_threshold: uint8
#     required_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs
#     optional_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs


# struct ULNReadConfig:
#     executor: address
#     required_dvn_count: uint8
#     optional_dvn_count: uint8
#     optional_dvn_threshold: uint8
#     required_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs
#     optional_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs


# struct ULNExecutorConfig:
#     max_message_size: uint32
#     executor: address


################################################################
#                         CONSTRUCTOR                          #
################################################################

@deploy
def __init__(_endpoint: address, _delegate: address):
    """
    @notice Initialize OApp with endpoint and delegate
    @param _endpoint LayerZero endpoint address
    @param _delegate Address that can manage LZ configurations
    """
    assert _endpoint != empty(address), "Invalid endpoint"
    assert _delegate != empty(address), "Invalid delegate"

    # Set up endpoint
    ENDPOINT = ILayerZeroEndpointV2(_endpoint)

    # Set delegate for endpoint config
    extcall ENDPOINT.setDelegate(_delegate)

    # Set up owner to tx.origin (if deploy via proxy)
    ownable.__init__()
    ownable._transfer_ownership(tx.origin)


################################################################
#                           OAppCore                           #
################################################################

@external
def setPeer(_eid: uint32, _peer: bytes32):
    """
    @notice Sets the peer address (OApp instance) for a corresponding endpoint.
    @param _eid The endpoint ID.
    @param _peer The address of the peer to be associated with the corresponding endpoint.
    @dev Only the owner/admin of the OApp can call this function.
    @dev Indicates that the peer is trusted to send LayerZero messages to this OApp.
    @dev Set this to bytes32(0) to remove the peer address.
    @dev Peer is a bytes32 to accommodate non-evm chains.
    """
    ownable._check_owner()

    self._setPeer(_eid, _peer)


@internal
def _setPeer(_eid: uint32, _peer: bytes32):
    """
    @notice Internal function to set peer address
    @param _eid The endpoint ID.
    @param _peer The address of the peer to be associated with the corresponding endpoint.
    """
    self.peers[_eid] = _peer

    log PeerSet(eid=_eid, peer=_peer)


@view
@internal
def _getPeerOrRevert(_eid: uint32) -> bytes32:
    """
    @notice Internal function to get the peer address associated with a specific endpoint;
    reverts if NOT set.
    @param _eid The endpoint ID.
    @return peer The address of the peer associated with the specified endpoint.
    """
    peer: bytes32 = self.peers[_eid]
    assert peer != empty(bytes32), "OApp: no peer"
    return peer


@external
def setDelegate(_delegate: address):
    """
    @notice Sets the delegate address for the OApp.
    @param _delegate The address of the delegate to be set.
    @dev Only the owner/admin of the OApp can call this function.
    @dev Provides the ability for a delegate to set configs, on behalf of the OApp, directly on the Endpoint contract.
    """
    ownable._check_owner()

    extcall ENDPOINT.setDelegate(_delegate)


################################################################
#                           OAppRead                           #
################################################################

@external
def setReadChannel(_channelId: uint32, _active: bool):
    """
    @notice Set or unset a read channel for this OApp
    @param _channelId The channel ID to use for read requests
    @param _active Whether to activate or deactivate the channel
    """
    ownable._check_owner()

    peer: bytes32 = convert(self, bytes32) if _active else convert(empty(address), bytes32)
    self._setPeer(_channelId, peer)


################################################################
#                         OAppReceiver                         #
################################################################

# Vyper-specific:
# oAppVersion - not implemented
# isComposeMsgSender - not implemented

@view
@external
def allowInitializePath(_origin: Origin) -> bool:
    """
    @notice Checks if the path initialization is allowed based on the provided origin.
    @param _origin The origin information containing the source endpoint and sender address.
    @return Whether the path has been initialized.
    @dev This indicates to the endpoint that the OApp has enabled msgs for this particular path to be received.
    @dev This defaults to assuming if a peer has been set, its initialized.
    """
    return self.peers[_origin.srcEid] == _origin.sender


@view
@external
def nextNonce(_srcEid: uint32, _sender: bytes32) -> uint64:
    """
    @notice Retrieves the next nonce for a given source endpoint and sender address.
    @dev _srcEid The source endpoint ID.
    @dev _sender The sender address.
    @return nonce The next nonce.
    @dev The path nonce starts from 1. If 0 is returned it means that there is NO nonce ordered enforcement.
    @dev Is required by the off-chain executor to determine the OApp expects msg execution is ordered.
    @dev This is also enforced by the OApp.
    @dev By default this is NOT enabled. ie. nextNonce is hardcoded to return 0.

    @dev Vyper-specific: If your app relies on ordered execution, you must change this function.
    """
    return 0


@internal
def lzReceive(
    _origin: Origin,
    _guid: bytes32,
    _message: Bytes[MAX_MESSAGE_SIZE],
    _executor: address,
    _extraData: Bytes[MAX_EXTRA_DATA_SIZE],
):
    """
    @dev Vyper-specific: This must be called first in external lzReceive implementation.

    @notice Entry point for receiving messages or packets from the endpoint.
    @param _origin The origin information containing the source endpoint and sender address.
        - srcEid: The source chain endpoint ID.
        - sender: The sender address on the src chain.
        - nonce: The nonce of the message.
    @param _guid The unique identifier for the received LayerZero message.
    @param _message The payload of the received message.
    @param _executor The address of the executor for the received message.
    @param _extraData Additional arbitrary data provided by the corresponding executor.
    """
    # Verify that the sender is the endpoint
    assert msg.sender == ENDPOINT.address, "OApp: only endpoint"

    # Verify that the message comes from a trusted peer
    assert self._getPeerOrRevert(_origin.srcEid) == _origin.sender, "OApp: invalid sender"


################################################################
#                         OAppSender                           #
################################################################

# Vyper-specific:
# oAppVersion - not implemented


@view
@internal
def _quote(
    _dstEid: uint32,
    _message: Bytes[MAX_MESSAGE_SIZE],
    _options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE],
    _payInLzToken: bool,
) -> MessagingFee:
    """
    @dev Internal function to interact with the LayerZero EndpointV2.quote() for fee calculation.
    @param _dstEid The destination endpoint ID.
    @param _message The message payload.
    @param _options Additional options for the message.
    @param _payInLzToken Flag indicating whether to pay the fee in LZ tokens.
    @return fee The calculated MessagingFee for the message.
            - nativeFee: The native fee for the message.
            - lzTokenFee: The LZ token fee for the message.
    """

    return staticcall ENDPOINT.quote(
        MessagingParams(
            dstEid=_dstEid,
            receiver=self._getPeerOrRevert(_dstEid),
            message=_message,
            options=_options,
            payInLzToken=_payInLzToken,
        ),
        self,
    )


@payable
@internal
def _lzSend(
    _dstEid: uint32,
    _message: Bytes[MAX_MESSAGE_SIZE],
    _options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE],
    _fee: MessagingFee,
    _refundAddress: address,
) -> MessagingReceipt:
    """
    @dev Internal function to interact with the LayerZero EndpointV2.send() for sending a message.
    @param _dstEid The destination endpoint ID.
    @param _message The message payload.
    @param _options Additional options for the message.
    @param _fee The calculated LayerZero fee for the message.
        - nativeFee: The native fee.
        - lzTokenFee: The lzToken fee.
    @param _refundAddress The address to receive any excess fee values sent to the endpoint.
    @return receipt The receipt for the sent message.
        - guid: The unique identifier for the sent message.
        - nonce: The nonce of the sent message.
        - fee: The LayerZero fee incurred for the message.

    @dev Vyper-specific: fees are treated differently than in Solidity OApp.
        - _payNative and _payLzToken are inlined.
        - Multiple sends are supported within single transaction (msg.value >= native_fee) instead of '!='.
    """
    # Get the peer address for the destination or revert if not set
    peer: bytes32 = self._getPeerOrRevert(_dstEid)

    # Handle native fee
    native_fee: uint256 = _fee.nativeFee
    if native_fee > 0:
        assert msg.value >= native_fee, "OApp: not enough fee"

    lzToken_fee: uint256 = _fee.lzTokenFee
    if lzToken_fee > 0:
        lzToken: address = staticcall ENDPOINT.lzToken()
        assert lzToken != empty(address), "OApp: LZ token unavailable"
        extcall IERC20(lzToken).transferFrom(msg.sender, ENDPOINT.address, lzToken_fee)

    return extcall ENDPOINT.send(
        MessagingParams(
            dstEid=_dstEid,
            receiver=peer,
            message=_message,
            options=_options,
            payInLzToken=_fee.lzTokenFee > 0,
        ),
        _refundAddress,
        value=native_fee,
    )


# ################################################################
# #                     ReadCmdCodecV1 LIBRARY                   #
# ################################################################

# @internal
# @pure
# def _encodeEVMCallRequestV1(_request: EVMCallRequestV1) -> Bytes[MAX_MESSAGE_SIZE]:
#     """
#     @notice Encodes a single EVM call request
#     @param _request The EVM call request to encode
#     @return Encoded request
#     """
#     # Calculate request size (35 bytes fixed + variable calldata)
#     request_size: uint16 = convert(len(_request.callData) + 35, uint16)

#     # Build header in smaller chunks to control byte sizes
#     header_part1: Bytes[5] = concat(
#         convert(REQUEST_VERSION, bytes1),  # request version
#         convert(_request.appRequestLabel, bytes2),  # app request label
#         convert(RESOLVER_TYPE_SINGLE_VIEW_EVM_CALL, bytes2),  # resolver type
#     )
#     header_part2: Bytes[7] = concat(
#         convert(request_size, bytes2),  # payload size
#         convert(_request.targetEid, bytes4),  # target EID
#         convert(_request.isBlockNum, bytes1),  # isBlockNum flag
#     )

#     # Combine all parts
#     header: Bytes[20] = concat(
#         header_part1,
#         header_part2,
#         convert(_request.blockNumOrTimestamp, bytes8),  # block number or timestamp
#     )

#     # Encode the rest of the request
#     request: Bytes[MAX_MESSAGE_SIZE] = concat(
#         header,
#         convert(_request.confirmations, bytes2),  # confirmations
#         convert(_request.to, bytes20),  # target address
#         _request.callData,  # call data
#     )
#     return request


# @internal
# @pure
# def _encodeReadCmd(
#     _request: EVMCallRequestV1,
#     _appCmdLabel: uint16 = 0,
# ) -> Bytes[MAX_MESSAGE_SIZE]:
#     """
#     @notice Creates a simplified read command (single request only)
#     @param _appCmdLabel Application command label
#     @param _request EVM call request
#     @return Encoded read command
#     """

#     # Calculate request size (35 bytes of fixed fields + calldata)
#     request_size: uint16 = convert(len(_request.callData) + 35, uint16)

#     # Build parts of the header
#     # First 6 bytes: command version, app cmd label, request count
#     cmd_header: Bytes[6] = concat(
#         convert(CMD_VERSION, bytes2),  # version = 1
#         convert(_appCmdLabel, bytes2),  # app command label
#         convert(1, bytes2),  # requests length = 1
#     )

#     # The request header (13 bytes)
#     request_header: Bytes[13] = concat(
#         convert(REQUEST_VERSION, bytes1),  # version = 1
#         convert(_request.appRequestLabel, bytes2),  # request label
#         convert(RESOLVER_TYPE_SINGLE_VIEW_EVM_CALL, bytes2),  # resolver type
#         convert(request_size, bytes2),  # payload size
#         convert(_request.targetEid, bytes4),  # target EID
#         convert(request.isBlockNum, bytes1),  # isBlockNum flag
#     )

#     # Build the request body
#     request_body: Bytes[MAX_MESSAGE_SIZE - 19] = concat(
#         convert(request.blockNumOrTimestamp, bytes8),  # block number or timestamp
#         convert(request.confirmations, bytes2),  # confirmations
#         convert(request.to, bytes20),  # target address
#         request.callData,  # call data
#     )

#     # Combine all parts - but we build it in steps to manage size
#     part1: Bytes[19] = concat(cmd_header, request_header)

#     # Return the complete message
#     return concat(part1, request_body)


# ################################################################
# #                    CONFIGURATION FUNCTIONS                   #
# ################################################################

# @external
# def setConfig(_lib: address, _eid: uint32, _configType: uint32, _config: Bytes[1024]):
#     """
#     @notice Set configuration parameters for the endpoint
#     @param _lib The library address
#     @param _eid The endpoint ID
#     @param _configType The configuration type
#     @param _config The configuration data
#     """
#     # Create config param
#     config_param: SetConfigParam = SetConfigParam(eid=_eid, configType=_configType, config=_config)

#     # Call endpoint to set config
#     extcall ENDPOINT.setConfig(self, _lib, [config_param])


# @external
# def setSendLibrary(_eid: uint32, _lib: address):
#     """
#     @notice Set the send library for a specific endpoint
#     @param _eid The endpoint ID
#     @param _lib The send library address
#     """
#     extcall ENDPOINT.setSendLibrary(self, _eid, _lib)


# @external
# def setReceiveLibrary(_eid: uint32, _lib: address, _gracePeriod: uint256 = 0):
#     """
#     @notice Set the receive library for a specific endpoint
#     @param _eid The endpoint ID
#     @param _lib The receive library address
#     @param _gracePeriod The grace period for the library change
#     """
#     extcall ENDPOINT.setReceiveLibrary(self, _eid, _lib, _gracePeriod)


# @external
# def setULNConfig(
#     _eid: uint32,
#     _lib: address,
#     _configType: uint32,
#     _confirmations: uint64,
#     _required_dvns: DynArray[address, MAX_DVNS],
#     _optional_dvns: DynArray[address, MAX_DVNS],
#     _optional_dvn_threshold: uint8,
#     _executor: address = empty(address),
# ):
#     """
#     @notice Set ULN configuration for a specific endpoint
#     @param _eid The endpoint ID
#     @param _lib The library address
#     @param _configType The configuration type
#     @param _confirmations The number of confirmations required
#     @param _required_dvns List of required DVN addresses
#     @param _optional_dvns List of optional DVN addresses
#     @param _optional_dvn_threshold Optional DVN threshold
#     @param _executor Executor address
#     """
#     # Prepare ULN config
#     required_count: uint8 = convert(len(_required_dvns), uint8)
#     optional_count: uint8 = convert(len(_optional_dvns), uint8)
#     assert _optional_dvn_threshold <= optional_count, "Invalid DVN threshold"

#     # Declare config_param outside of if/else
#     config_param: SetConfigParam = empty(SetConfigParam)

#     # For read config
#     if _eid > READ_CHANNEL_THRESHOLD:
#         uln_config: ULNReadConfig = ULNReadConfig(
#             executor=_executor,
#             required_dvn_count=required_count,
#             optional_dvn_count=optional_count,
#             optional_dvn_threshold=_optional_dvn_threshold,
#             required_dvns=_required_dvns,
#             optional_dvns=_optional_dvns,
#         )
#         config_param = SetConfigParam(
#             eid=_eid, configType=_configType, config=abi_encode(uln_config)
#         )
#     else:
#         # For regular config
#         uln_config: ULNConfig = ULNConfig(
#             confirmations=_confirmations,
#             required_dvn_count=required_count,
#             optional_dvn_count=optional_count,
#             optional_dvn_threshold=_optional_dvn_threshold,
#             required_dvns=_required_dvns,
#             optional_dvns=_optional_dvns,
#         )
#         config_param = SetConfigParam(
#             eid=_eid, configType=_configType, config=abi_encode(uln_config)
#         )


#     # Call endpoint to set config
#     extcall ENDPOINT.setConfig(self, _lib, [config_param])

#     # Set executor config if provided for normal channels
#     if _executor != empty(address) and _eid <= READ_CHANNEL_THRESHOLD:
#         executor_config: ULNExecutorConfig = ULNExecutorConfig(
#             max_message_size=1024, executor=_executor
#         )

#         # Reuse config_param for executor config
#         config_param = SetConfigParam(
#             eid=_eid, configType=1, config=abi_encode(executor_config)  # 1 = ULN executor config
#         )
#         extcall ENDPOINT.setConfig(self, _lib, [config_param])


################################################################
#                     Offspec Utilities                        #
################################################################

@external
def skipInboundNonce(_srcEid: uint32, _sender: bytes32, _nonce: uint64):
    """
    @notice Owner function to skip nonce (in case of stuck messages)
    @param _srcEid The source endpoint ID
    @param _sender The sender bytes32 address
    @param _nonce The nonce to skip
    """
    ownable._check_owner()

    extcall ENDPOINT.skip(self, _srcEid, _sender, _nonce)
