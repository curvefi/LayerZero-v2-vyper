# pragma version ~=0.4

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
from LZModule import OApp
initializes: OApp[ownable:=ownable]

from LZModule import OAppConfigUtils
initializes: OAppConfigUtils[ownable:=ownable]

from LZModule import OptionsBuilder
from LZModule import ReadCmdCodecV1

################################################################
#                            EVENTS                            #
################################################################

event MessageSent:
    destination: uint32
    payload: String[128]
    fees: uint256


event MessageReceived:
    source: uint32
    payload: String[128]


event ReadRequestSent:
    destination: uint32
    target: address
    payload: Bytes[128]


event ReadResponseReceived:
    source: uint32
    response: String[128]


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
    OAppConfigUtils.__init__(_endpoint)


@external
def withdraw_eth(_amount: uint256):
    """
    @notice Withdraw ETH from contract
    @param _amount Amount to withdraw
    """

    ownable._check_owner()
    assert self.balance >= _amount, "Insufficient balance"
    send(msg.sender, _amount)


# ################################################################
# #                    MESSAGING FUNCTIONS                       #
# ################################################################

# @view
# @external
# def quote_message_fee(
#     _dst_eid: uint32,
#     _receiver: address,
#     _message: String[128],
#     _gas_limit: uint256 = 0,
#     _value: uint256 = 0,
# ) -> uint256:
#     """
#     @notice Quote fee for sending message
#     """

#     encoded: Bytes[OApp.MAX_MESSAGE_SIZE] = convert(_message, Bytes[OApp.MAX_MESSAGE_SIZE])
#     return OApp._quote_lz_fee(_dst_eid, _receiver, encoded, _gas_limit, _value)


# @payable
# @external
# def send_message(
#     _dst_eid: uint32,
#     _receiver: address,
#     _message: String[128],
#     _gas_limit: uint256 = 0,
#     _value: uint256 = 0,
#     _check_fee: bool = False,
# ):
#     """
#     @notice Send a string message to contract on another chain
#     @param _dst_eid Destination chain ID
#     @param _receiver Target contract address
#     @param _message String message to send
#     @param _gas_limit Optional gas limit override
#     @param _value Optional value to send with message
#     """

#     encoded: Bytes[lz.LZ_MESSAGE_SIZE_CAP] = convert(_message, Bytes[lz.LZ_MESSAGE_SIZE_CAP])
#     lz._send_message(
#         _dst_eid,  # _dstEid
#         convert(_receiver, bytes32),  # _receiver
#         encoded,  # _message
#         _gas_limit,  # _gas_limit: Use default gas limit
#         _value,  # _lz_receive_value: No value to attach to receive call
#         0,  # _data_size: Zero data size (not a read)
#         msg.value,  # _request_msg_value
#         msg.sender,  # _refund_address
#         False,  # _perform_fee_check: No fee check
#     )

#     log MessageSent(_dst_eid, _message, msg.value)


# @view
# @external
# def quote_read_fee(
#     _dst_eid: uint32,
#     _target: address,
#     _calldata: Bytes[128],
#     _gas_limit: uint256 = 0,
#     _value: uint256 = 0,
#     _data_size: uint32 = 64,
# ) -> uint256:
#     """
#     @notice Quote fee for read request
#     """

#     message: Bytes[lz.LZ_MESSAGE_SIZE_CAP] = lz._prepare_read_message_bytes(
#         _dst_eid, _target, _calldata
#     )

#     return lz._quote_lz_fee(
#         lz.LZ_READ_CHANNEL, empty(address), message, _gas_limit, _value, _data_size
#     )


# @payable
# @external
# def request_read(
#     _dst_eid: uint32,
#     _target: address,
#     _calldata: Bytes[128],
#     _gas_limit: uint256 = 0,
#     _value: uint256 = 0,
#     _data_size: uint32 = 64,
#     _check_fee: bool = False,
# ):
#     """
#     @notice Send read request to another chain
#     @param _dst_eid Target chain endpoint ID
#     @param _target Contract to read from
#     @param _calldata Function call data
#     @param _gas_limit Optional gas limit
#     @param _value Optional value to send with message
#     @param _data_size Expected response size
#     @param _check_fee Validate sufficent fee before sending
#     """

#     # Prepare read message
#     message: Bytes[lz.LZ_MESSAGE_SIZE_CAP] = lz._prepare_read_message_bytes(
#         _dst_eid, _target, _calldata, False, convert(block.timestamp, uint64), 1
#     )

#     # Send to read channel
#     lz._send_message(
#         lz.LZ_READ_CHANNEL,  # _dstEid
#         convert(self, bytes32),  # _receiver
#         message,  # _message
#         _gas_limit,  # _gas_limit: Use default gas limit
#         _value,  # _lz_receive_value: Will be available in lzReceive (and pay for broadcasts)
#         _data_size,  # _data_size: Expected read size (uint256: block number, bytes32: block hash)
#         msg.value,  # _request_msg_value: Use cached fee as send message value
#         msg.sender,  # _refund_address: Refund unspent fees to read requestor
#         _check_fee,  # _perform_fee_check: No fee check
#     )

#     log ReadRequestSent(_dst_eid, _target, _calldata)


# @payable
# @external
# def lzReceive(
#     _origin: lz.Origin,
#     _guid: bytes32,
#     _message: Bytes[lz.LZ_MESSAGE_SIZE_CAP],
#     _executor: address,
#     _extraData: Bytes[64],
# ) -> bool:
#     """
#     @notice Handle both regular messages and read responses
#     """

#     # Verify message source
#     assert lz._lz_receive(_origin, _guid, _message, _executor, _extraData)

#     if lz._is_read_response(_origin):
#         # Handle read response
#         message: String[128] = convert(_message, String[128])
#         log ReadResponseReceived(_origin.srcEid, message)
#     else:
#         # Handle regular message
#         message: String[128] = convert(_message, String[128])
#         log MessageReceived(_origin.srcEid, message)

#     return True


# @view
# @external
# def dummy_endpoint(_input: uint256) -> uint256:
#     return 2 * _input


# @external
# @payable
# def __default__():
#     """
#     @notice Default function to receive ETH
#     @dev This is needed to receive refunds from LayerZero
#     """
#     pass
