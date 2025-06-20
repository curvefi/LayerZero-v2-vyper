# pragma version 0.4.3

"""
@title Example LayerZero Messenger

@notice Example implementation of LZ Base module for simple messaging between
chains. Allows sending and receiving string messages across chains using LayerZero
protocol. Includes ownership control for secure peer management and configuration.

@license Copyright (c) Curve.Fi, 2025 - all rights reserved

@author curve.fi

@custom:security security@curve.fi

"""

################################################################
#                           MODULES                            #
################################################################

# Import ownership management
from snekmate.auth import ownable

initializes: ownable
exports: (
    ownable.owner,
    ownable.transfer_ownership,
    ownable.renounce_ownership,
)

# LayerZero module
from ..src import OApp

initializes: OApp[ownable := ownable]
exports: (
    OApp.endpoint,
    OApp.peers,
    OApp.setPeer,
    OApp.setDelegate,
    OApp.setReadChannel,
    OApp.isComposeMsgSender,
    OApp.allowInitializePath,
    OApp.nextNonce,
)

from ..src import OptionsBuilder
from ..src import ReadCmdCodecV1

################################################################
#                            EVENTS                            #
################################################################

event MessageSent:
    destination: uint32
    payload: String[OApp.MAX_MESSAGE_SIZE]
    fees: OApp.MessagingFee


event MessageReceived:
    source: uint32
    payload: String[OApp.MAX_MESSAGE_SIZE]


event ReadRequestSent:
    destination: uint32
    target: address
    payload: Bytes[ReadCmdCodecV1.MAX_MESSAGE_SIZE]


event ReadResponseReceived:
    source: uint32
    response: String[OApp.MAX_MESSAGE_SIZE]


################################################################
#                          CONSTRUCTOR                         #
################################################################

@deploy
def __init__(_endpoint: address):
    """
    @notice Initialize messenger with LZ endpoint and default gas settings
    @param _endpoint LayerZero endpoint address
    """
    ownable.__init__()
    ownable._transfer_ownership(tx.origin)

    OApp.__init__(_endpoint, tx.origin)


@external
def withdraw_eth(_amount: uint256):
    """
    @notice Withdraw ETH from contract
    @param _amount Amount to withdraw
    """

    ownable._check_owner()
    assert self.balance >= _amount, "Insufficient balance"
    send(msg.sender, _amount)


################################################################
#                    MESSAGING FUNCTIONS                       #
# ##############################################################

@view
@external
def quote_message_fee(
    _dst_eid: uint32,
    _receiver: address,
    _message: String[128],
    _gas_limit: uint128 = 0,
    _value: uint128 = 0,
    _pay_in_lz_token: bool = False,
) -> OApp.MessagingFee:

    # step 1: convert message to bytes
    encoded_message: Bytes[OApp.MAX_MESSAGE_SIZE] = convert(_message, Bytes[OApp.MAX_MESSAGE_SIZE])

    # step 2: create options using OptionsBuilder module
    options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE] = OptionsBuilder.newOptions()
    options = OptionsBuilder.addExecutorLzReceiveOption(options, _gas_limit, _value)

    # step 3: quote fee
    return OApp._quote(_dst_eid, encoded_message, options, _pay_in_lz_token)


@payable
@external
def send_message(
    _dst_eid: uint32,
    _receiver: address,
    _message: String[128],
    _gas_limit: uint128 = 0,
    _value: uint128 = 0,
    _lz_token_fee: uint256 = 0,
):
    """
    @notice Send a string message to contract on another chain
    @param _dst_eid Destination chain ID
    @param _receiver Target contract address
    @param _message String message to send
    @param _gas_limit Optional gas limit override
    @param _value Optional value to send with message
    """
    # step 1: convert message to bytes
    encoded_message: Bytes[OApp.MAX_MESSAGE_SIZE] = convert(_message, Bytes[OApp.MAX_MESSAGE_SIZE])

    # step 2: create options using OptionsBuilder module
    options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE] = OptionsBuilder.newOptions()
    options = OptionsBuilder.addExecutorLzReceiveOption(options, _gas_limit, _value)

    # # step 3: send message
    fees: OApp.MessagingFee = OApp.MessagingFee(nativeFee=msg.value, lzTokenFee=_lz_token_fee)
    OApp._lzSend(_dst_eid, encoded_message, options, fees, msg.sender)

    log MessageSent(destination=_dst_eid, payload=_message, fees=fees)


@view
@external
def quote_read_fee(
    _read_channel_id: uint32,
    _dst_eid: uint32,
    _target: address,
    _calldata: Bytes[ReadCmdCodecV1.MAX_CALLDATA_SIZE],
    _gas_limit: uint128 = 0,
    _value: uint128 = 0,
    _expected_response_size: uint32 = 64,
    _pay_in_lz_token: bool = False,
) -> OApp.MessagingFee:
    """
    @notice Quote fee for read request
    """

    # step 1: prepare read message using ReadCmdCodecV1 module
    # A: prepare ReadCmdRequestV1 struct
    request: ReadCmdCodecV1.EVMCallRequestV1 = ReadCmdCodecV1.EVMCallRequestV1(
        appRequestLabel=0,
        targetEid=_dst_eid,
        isBlockNum=False,
        blockNumOrTimestamp=convert(block.timestamp, uint64),
        confirmations=0,
        to=_target,
        callData=_calldata,
    )
    # B: encode request
    encoded_message: Bytes[ReadCmdCodecV1.MAX_MESSAGE_SIZE] = ReadCmdCodecV1.encode(0, [request])

    # step 2: create options using OptionsBuilder module
    options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE] = OptionsBuilder.newOptions()
    options = OptionsBuilder.addExecutorLzReadOption(
        options, _gas_limit, _expected_response_size, _value
    )

    # step 3: quote fee
    return OApp._quote(_read_channel_id, encoded_message, options, _pay_in_lz_token)


@payable
@external
def request_read(
    _read_channel_id: uint32,
    _dst_eid: uint32,
    _target: address,
    _calldata: Bytes[ReadCmdCodecV1.MAX_CALLDATA_SIZE],
    _gas_limit: uint128 = 0,
    _value: uint128 = 0,
    _expected_response_size: uint32 = 64,
    _lz_token_fee: uint256 = 0,
):
    """
    @notice Send read request to another chain
    @param _dst_eid Target chain endpoint ID
    @param _target Contract to read from
    @param _calldata Function call data
    @param _gas_limit Optional gas limit
    @param _value Optional value to send with message
    @param _expected_response_size Expected response size
    @param _lz_token_fee Optional LZ token fee
    """

    # step 1: prepare read message using ReadCmdCodecV1 module
    # A: prepare ReadCmdRequestV1 struct
    request: ReadCmdCodecV1.EVMCallRequestV1 = ReadCmdCodecV1.EVMCallRequestV1(
        appRequestLabel=0,
        targetEid=_dst_eid,
        isBlockNum=False,
        blockNumOrTimestamp=convert(block.timestamp, uint64),
        confirmations=0,
        to=_target,
        callData=_calldata,
    )

    # B: encode request
    encoded_message: Bytes[ReadCmdCodecV1.MAX_MESSAGE_SIZE] = ReadCmdCodecV1.encode(0, [request])

    # step 2: create options using OptionsBuilder module
    options: Bytes[OptionsBuilder.MAX_OPTIONS_TOTAL_SIZE] = OptionsBuilder.newOptions()
    options = OptionsBuilder.addExecutorLzReadOption(
        options, _gas_limit, _expected_response_size, _value
    )

    # step 3: send message
    fees: OApp.MessagingFee = OApp.MessagingFee(nativeFee=msg.value, lzTokenFee=_lz_token_fee)
    OApp._lzSend(_read_channel_id, encoded_message, options, fees, msg.sender)

    log ReadRequestSent(destination=_read_channel_id, target=_target, payload=encoded_message)


@external
@payable
def lzReceive(
    _origin: OApp.Origin,
    _guid: bytes32,
    _message: Bytes[OApp.MAX_MESSAGE_SIZE],
    _executor: address,
    _extraData: Bytes[OApp.MAX_EXTRA_DATA_SIZE],
):
    """
    @notice Handle both regular messages and read responses
    """

    # Basic parameter validation for message source
    OApp._lzReceive(_origin, _guid, _message, _executor, _extraData)

    if _origin.srcEid > OApp.READ_CHANNEL_THRESHOLD:
        # Handle read response
        message: String[OApp.MAX_MESSAGE_SIZE] = convert(_message, String[OApp.MAX_MESSAGE_SIZE])
        log ReadResponseReceived(source=_origin.srcEid, response=message)
    else:
        # Handle regular message
        message: String[OApp.MAX_MESSAGE_SIZE] = convert(_message, String[OApp.MAX_MESSAGE_SIZE])
        log MessageReceived(source=_origin.srcEid, payload=message)


@view
@external
def dummy_endpoint(_input: uint256) -> uint256:
    return 2 * _input


@external
@payable
def __default__():
    """
    @notice Default function to receive ETH
    @dev This might be needed to receive refunds from LayerZero (for complex lzsend/receive patterns)
    """
    pass
