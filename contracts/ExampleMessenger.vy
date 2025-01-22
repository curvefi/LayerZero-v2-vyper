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
def lzReceive(
    _origin: lz.Origin,
    _guid: bytes32,
    _message: Bytes[lz.LZ_MESSAGE_SIZE_CAP],
    _executor: address,
    _extraData: Bytes[64],
) -> bool:
    """
    @notice Handle incoming messages from other chains
    @dev Verifies sender and converts message back to string
    """
    # Verify message source
    assert lz._lz_receive(_origin, _guid, _message, _executor, _extraData)

    # Convert and store message
    message: String[128] = convert(_message, String[128])
    log MessageReceived(_origin.srcEid, message)

    return True
