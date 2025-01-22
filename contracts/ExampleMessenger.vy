# pragma version ~=0.4

"""
@title Example LayerZero Messenger

@notice Example implementation of LZ Base module for simple messaging between
chains. Allows sending and receiving string messages across chains using LayerZero
protocol. Includes ownership control for secure peer management and configuration.

@dev
- Uses LZ Base module for core messaging functionality
- Implements both sending and receiving of string messages
- Includes ownable_2step for secure management
- Messages are limited to 128 bytes and converted between string/bytes

@author curve.fi
"""


################################################################
#                           INTERFACES                         #
################################################################


# Import LayerZero module for cross-chain messaging
import LayerZeroV2 as lz
initializes: lz
exports: (
    lz.LZ_ENDPOINT,
    lz.LZ_PEERS,
    lz.LZ_MESSAGE_SIZE_CAP,
    lz.LZ_READ_CALLDATA_SIZE,
    lz.default_gas_limit,
    lz.quote_lz_fee,
    lz.nextNonce,
    lz.allowInitializePath,
)

# Import ownership management
from snekmate.auth import ownable
from snekmate.auth import ownable_2step

initializes: ownable
initializes: ownable_2step[ownable := ownable]
exports: (
    ownable_2step.owner,
    ownable_2step.pending_owner,
    ownable_2step.transfer_ownership,
    ownable_2step.accept_ownership,
    ownable_2step.renounce_ownership,
)


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
def __init__(_endpoint: address, _gas_limit: uint256):
    """
    @notice Initialize messenger with LZ endpoint and default gas settings
    @param _endpoint LayerZero endpoint address
    @param _gas_limit Default gas limit for cross-chain messages
    """
    # Initialize all modules
    lz.__init__(_endpoint, _gas_limit)
    ownable.__init__()
    ownable_2step.__init__()


################################################################
#                      OWNER FUNCTIONS                         #
################################################################


@external
def set_peer(_srcEid: uint32, _peer: address):
    """
    @notice Set trusted peer contract on another chain
    @param _srcEid Target endpoint ID
    @param _peer Contract address on target chain
    """
    ownable._check_owner()
    lz._set_peer(_srcEid, _peer)


@external
def set_default_gas(_gas_limit: uint256):
    """
    @notice Update default gas limit for messages
    @param _gas_limit New gas limit
    """
    ownable._check_owner()
    lz._set_default_gas_limit(_gas_limit)


################################################################
#                    MESSAGING FUNCTIONS                       #
################################################################


@payable
@external
def send_message(
    _dst_eid: uint32, _receiver: address, _message: String[128], _gas_limit: uint256 = 0
):
    """
    @notice Send a string message to contract on another chain
    @param _dst_eid Destination chain ID
    @param _receiver Target contract address
    @param _message String message to send
    @param _gas_limit Optional gas limit override
    """
    encoded: Bytes[lz.LZ_MESSAGE_SIZE_CAP] = convert(_message, Bytes[lz.LZ_MESSAGE_SIZE_CAP])
    lz._send_message(_dst_eid, _receiver, encoded, _gas_limit)
    log MessageSent(_dst_eid, _message, msg.value)


@payable
@external
def read_remote_storage(
    _dst_eid: uint32,
    _target: address,
    _calldata: Bytes[128],
    _gas_limit: uint256 = 0,
    _data_size: uint32 = 64,
):
    """
    @notice Send read request to another chain
    @param _dst_eid Target chain ID
    @param _target Contract to read from
    @param _calldata Function call data
    @param _gas_limit Optional gas limit
    @param _data_size Expected response size
    """
    request: lz.EVMCallRequestV1 = lz.EVMCallRequestV1(
        appRequestLabel=1,
        targetEid=_dst_eid,
        isBlockNum=False,  # Use latest state
        blockNumOrTimestamp=convert(block.timestamp, uint64),
        confirmations=15,
        to=_target,
        callData=_calldata,
    )

    # Send read request
    lz._send_read_request(request, _gas_limit, _data_size)
    log ReadRequestSent(_dst_eid, _target, _calldata)


@payable
@external
def lzReceive(
    _origin: lz.Origin,
    _guid: bytes32,
    _message: Bytes[lz.LZ_MESSAGE_SIZE_CAP],
    _executor: address,
    _extraData: Bytes[64],
) -> bool:
    """
    @notice Handle both regular messages and read responses
    """
    # Verify message source
    assert lz._lz_receive(_origin, _guid, _message, _executor, _extraData)

    if _origin.srcEid > lz.READ_CHANNEL_THRESHOLD:
        # Handle read response
        message: String[128] = convert(_message, String[128])
        log ReadResponseReceived(_origin.srcEid, message)
    else:
        # Handle regular message
        message: String[128] = convert(_message, String[128])
        log MessageReceived(_origin.srcEid, message)

    return True


@view
@external
def quote_read_fee(
    _dst_eid: uint32,
    _target: address,
    _calldata: Bytes[128],
    _gas_limit: uint256 = 0,
    _data_size: uint32 = 64,
) -> uint256:
    """
    @notice Quote fee for read request
    @dev alternative wrapper that creates EVMCallRequestV1
    """
    request: lz.EVMCallRequestV1 = lz.EVMCallRequestV1(
        appRequestLabel=1,
        targetEid=_dst_eid,
        isBlockNum=False,
        blockNumOrTimestamp=convert(block.timestamp, uint64),
        confirmations=15,
        to=_target,
        callData=_calldata,
    )
    return lz._quote_lz_read_fee(request, _gas_limit, _data_size)
