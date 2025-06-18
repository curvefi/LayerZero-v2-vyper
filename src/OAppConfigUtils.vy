# pragma version 0.4.2

"""
@title LZConfig - LayerZero Configuration Manager

@notice Vyper implementation of the MessageLibManager functionality from LayerZero.
This module provides functions to set message libraries (send/receive) and other configurations
for OApps. This is meant to be called by the OApp owner.

@dev The functions in this module allow configuration of:
- Send libraries
- Receive libraries with grace periods
- DVN (ULN) configurations
- ULN Read configurations
- Executor configurations

@license Copyright (c) Curve.Fi, 2025 - all rights reserved

@author curve.fi

@custom:security security@curve.fi
"""

################################################################
#                            MODULES                           #
################################################################

# Import ownership management. Defer initialization to main contract.
from snekmate.auth import ownable

uses: ownable

# Vyper-specific constants
from . import VyperConstants as constants

################################################################
#                         INTERFACES                           #
################################################################

interface ILayerZeroEndpointV2:
    def setSendLibrary(_oapp: address, _eid: uint32, _newLib: address): nonpayable
    def setReceiveLibrary(
        _oapp: address, _eid: uint32, _newLib: address, _gracePeriod: uint256
    ): nonpayable
    def setConfig(
        _oapp: address, _lib: address, _params: DynArray[SetConfigParam, MAX_CONFIG_ITEMS]
    ): nonpayable
    def skip(_oapp: address, _srcEid: uint32, _sender: bytes32, _nonce: uint64): nonpayable


################################################################
#                           CONSTANTS                          #
################################################################

# Constants for DVN configuration
MAX_DVNS: constant(uint256) = constants.MAX_DVNS
MAX_CONFIG_ITEMS: constant(uint256) = constants.MAX_CONFIG_ITEMS

# Config types
CONFIG_TYPE_ULN: constant(uint32) = 0
CONFIG_TYPE_EXECUTOR: constant(uint32) = 1
CONFIG_TYPE_READ: constant(uint32) = 2


################################################################
#                           STORAGE                            #
################################################################

# Core contract state
ENDPOINT: public(immutable(ILayerZeroEndpointV2))


################################################################
#                           STRUCTS                            #
################################################################

struct SetConfigParam:
    eid: uint32
    configType: uint32
    config: Bytes[9 * 32 + 2 * MAX_DVNS * 32]  # 9 words for ULNConfig, 2*MAX_DVNS words for DVNs


struct Timeout:
    lib: address
    expiry: uint256


struct ULNConfig:
    confirmations: uint64
    required_dvn_count: uint8
    optional_dvn_count: uint8
    optional_dvn_threshold: uint8
    required_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs
    optional_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs


struct ULNReadConfig:
    executor: address
    required_dvn_count: uint8
    optional_dvn_count: uint8
    optional_dvn_threshold: uint8
    required_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs
    optional_dvns: DynArray[address, MAX_DVNS]  # Max 10 DVNs


struct ULNExecutorConfig:
    max_message_size: uint32
    executor: address


################################################################
#                         CONSTRUCTOR                          #
################################################################

@deploy
def __init__(_endpoint: address):
    """
    @notice Initialize LZConfig with endpoint address
    @param _endpoint LayerZero endpoint address
    """
    assert _endpoint != empty(address), "OAppConfig: Invalid endpoint"
    ENDPOINT = ILayerZeroEndpointV2(_endpoint)


################################################################
#                   LIBRARY MANAGEMENT FUNCTIONS               #
################################################################

@external
def setSendLibraries(
    _eids: DynArray[uint32, MAX_CONFIG_ITEMS], _newLibs: DynArray[address, MAX_CONFIG_ITEMS]
):
    """
    @notice Set multiple send libraries for this contract in a single transaction
    @param _eids Array of endpoint IDs
    @param _newLibs Array of new send library addresses (must match _eids length)
    """
    ownable._check_owner()

    assert len(_eids) == len(_newLibs), "OAppConfig: Array length mismatch"

    for i: uint256 in range(len(_eids), bound=MAX_CONFIG_ITEMS):
        extcall ENDPOINT.setSendLibrary(self, _eids[i], _newLibs[i])


@external
def setReceiveLibraries(
    _eids: DynArray[uint32, MAX_CONFIG_ITEMS],
    _newLibs: DynArray[address, MAX_CONFIG_ITEMS],
    _gracePeriods: DynArray[uint256, MAX_CONFIG_ITEMS],
):
    """
    @notice Set multiple receive libraries for this contract in a single transaction
    @param _eids Array of endpoint IDs
    @param _newLibs Array of new receive library addresses
    @param _gracePeriods Array of grace periods for the old libraries
    """
    ownable._check_owner()

    assert len(_eids) == len(_newLibs) and len(_eids) == len(
        _gracePeriods
    ), "OAppConfig: Array length mismatch"

    for i: uint256 in range(len(_eids), bound=MAX_CONFIG_ITEMS):
        extcall ENDPOINT.setReceiveLibrary(self, _eids[i], _newLibs[i], _gracePeriods[i])


################################################################
#                    DVN/ULN CONFIG FUNCTIONS                  #
################################################################

@external
def setUlnConfigs(
    _libs: DynArray[address, MAX_CONFIG_ITEMS],
    _eids: DynArray[uint32, MAX_CONFIG_ITEMS],
    _confirmations: DynArray[uint64, MAX_CONFIG_ITEMS],
    _optional_dvn_thresholds: DynArray[uint8, MAX_CONFIG_ITEMS],
    _required_dvns: DynArray[DynArray[address, MAX_DVNS], MAX_CONFIG_ITEMS],
    _optional_dvns: DynArray[DynArray[address, MAX_DVNS], MAX_CONFIG_ITEMS],
):
    """
    @notice Set multiple ULN (DVN) configurations in a single transaction
    @param _libs Array of library addresses
    @param _eids Array of endpoint IDs
    @param _confirmations Array of confirmation counts
    @param _optional_dvn_thresholds Array of optional DVN thresholds
    @param _required_dvns Nested array of required DVN addresses for each config
    @param _optional_dvns Nested array of optional DVN addresses for each config
    """
    ownable._check_owner()

    # Check array lengths match
    items_count: uint256 = len(_eids)
    assert len(_libs) == items_count, "OAppConfig: Array length mismatch: libs"
    assert len(_confirmations) == items_count, "OAppConfig: Array length mismatch: confirmations"
    assert (
        len(_optional_dvn_thresholds) == items_count
    ), "OAppConfig: Array length mismatch: thresholds"
    assert len(_required_dvns) == items_count, "OAppConfig: Array length mismatch: required DVNs"
    assert len(_optional_dvns) == items_count, "OAppConfig: Array length mismatch: optional DVNs"

    # Cap to max number of items we can process
    items_count = min(items_count, MAX_CONFIG_ITEMS)

    # Group configurations by lib for batch processing
    current_lib: address = empty(address)
    config_params: DynArray[SetConfigParam, MAX_CONFIG_ITEMS] = []
    for i: uint256 in range(items_count, bound=MAX_CONFIG_ITEMS):
        # Get DVN counts directly from array lengths
        required_count: uint8 = convert(len(_required_dvns[i]), uint8)
        optional_count: uint8 = convert(len(_optional_dvns[i]), uint8)

        # Verify threshold is valid
        assert _optional_dvn_thresholds[i] <= optional_count, "OAppConfig: Invalid DVN threshold"

        # Create the ULN config
        uln_config: ULNConfig = ULNConfig(
            confirmations=_confirmations[i],
            required_dvn_count=required_count,
            optional_dvn_count=optional_count,
            optional_dvn_threshold=_optional_dvn_thresholds[i],
            required_dvns=_required_dvns[i],
            optional_dvns=_optional_dvns[i],
        )

        # Create the config parameter
        config_param: SetConfigParam = SetConfigParam(
            eid=_eids[i], configType=CONFIG_TYPE_ULN, config=abi_encode(uln_config)
        )

        # If this is a new lib or the first item, start a new batch
        if _libs[i] != current_lib or i == 0:
            # Send the previous batch if not the first iteration
            if i > 0 and len(config_params) > 0:
                extcall ENDPOINT.setConfig(self, current_lib, config_params)

            current_lib = _libs[i]
            config_params = [config_param]
        else:
            # Add to current batch
            config_params.append(config_param)
        # Send the final batch if any params are left


    if len(config_params) > 0:
        extcall ENDPOINT.setConfig(self, current_lib, config_params)


@external
def setUlnReadConfigs(
    _libs: DynArray[address, MAX_CONFIG_ITEMS],
    _eids: DynArray[uint32, MAX_CONFIG_ITEMS],
    _executors: DynArray[address, MAX_CONFIG_ITEMS],
    _optional_dvn_thresholds: DynArray[uint8, MAX_CONFIG_ITEMS],
    _required_dvns: DynArray[DynArray[address, MAX_DVNS], MAX_CONFIG_ITEMS],
    _optional_dvns: DynArray[DynArray[address, MAX_DVNS], MAX_CONFIG_ITEMS],
):
    """
    @notice Set multiple ULN Read configurations in a single transaction
    @param _libs Array of library addresses
    @param _eids Array of endpoint IDs
    @param _executors Array of executor addresses
    @param _optional_dvn_thresholds Array of optional DVN thresholds
    @param _required_dvns Nested array of required DVN addresses for each config
    @param _optional_dvns Nested array of optional DVN addresses for each config
    """
    ownable._check_owner()

    # Check array lengths match
    items_count: uint256 = len(_eids)
    assert len(_libs) == items_count, "OAppConfig: Array length mismatch: libs"
    assert len(_executors) == items_count, "OAppConfig: Array length mismatch: executors"
    assert (
        len(_optional_dvn_thresholds) == items_count
    ), "OAppConfig: Array length mismatch: thresholds"
    assert len(_required_dvns) == items_count, "OAppConfig: Array length mismatch: required DVNs"
    assert len(_optional_dvns) == items_count, "OAppConfig: Array length mismatch: optional DVNs"

    # Cap to max number of items we can process
    items_count = min(items_count, MAX_CONFIG_ITEMS)

    # Group configurations by lib for batch processing
    current_lib: address = empty(address)
    config_params: DynArray[SetConfigParam, MAX_CONFIG_ITEMS] = []
    for i: uint256 in range(items_count, bound=MAX_CONFIG_ITEMS):

        # Get DVN counts directly from array lengths
        required_count: uint8 = convert(len(_required_dvns[i]), uint8)
        optional_count: uint8 = convert(len(_optional_dvns[i]), uint8)

        # Verify threshold is valid
        assert _optional_dvn_thresholds[i] <= optional_count, "OAppConfig: Invalid DVN threshold"

        # Create the ULN Read config
        uln_read_config: ULNReadConfig = ULNReadConfig(
            executor=_executors[i],
            required_dvn_count=required_count,
            optional_dvn_count=optional_count,
            optional_dvn_threshold=_optional_dvn_thresholds[i],
            required_dvns=_required_dvns[i],
            optional_dvns=_optional_dvns[i],
        )

        # Create the config parameter
        config_param: SetConfigParam = SetConfigParam(
            eid=_eids[i], configType=CONFIG_TYPE_READ, config=abi_encode(uln_read_config)
        )

        # If this is a new lib or the first item, start a new batch
        if _libs[i] != current_lib or i == 0:
            # Send the previous batch if not the first iteration
            if i > 0 and len(config_params) > 0:
                extcall ENDPOINT.setConfig(self, current_lib, config_params)

            current_lib = _libs[i]
            config_params = [config_param]
        else:
            # Add to current batch
            config_params.append(config_param)
        # Send the final batch if any params are left


    if len(config_params) > 0:
        extcall ENDPOINT.setConfig(self, current_lib, config_params)


@external
def setExecutorConfigs(
    _libs: DynArray[address, MAX_CONFIG_ITEMS],
    _eids: DynArray[uint32, MAX_CONFIG_ITEMS],
    _executors: DynArray[address, MAX_CONFIG_ITEMS],
):
    """
    @notice Set multiple executor configurations in a single transaction
    @param _libs Array of library addresses
    @param _eids Array of endpoint IDs
    @param _executors Array of executor addresses
    """
    ownable._check_owner()

    # Check array lengths match
    items_count: uint256 = len(_eids)
    assert len(_libs) == items_count, "OAppConfig: Array length mismatch: libs"
    assert len(_executors) == items_count, "OAppConfig: Array length mismatch: executors"

    # Cap to max number of items we can process
    items_count = min(items_count, MAX_CONFIG_ITEMS)

    # Group configurations by lib for batch processing
    current_lib: address = empty(address)
    config_params: DynArray[SetConfigParam, MAX_CONFIG_ITEMS] = []
    for i: uint256 in range(items_count, bound=MAX_CONFIG_ITEMS):
        # Create the Executor config
        executor_config: ULNExecutorConfig = ULNExecutorConfig(
            max_message_size=1024, executor=_executors[i]  # Default size, can be adjusted as needed
        )

        # Create the config parameter
        config_param: SetConfigParam = SetConfigParam(
            eid=_eids[i], configType=CONFIG_TYPE_EXECUTOR, config=abi_encode(executor_config)
        )

        # If this is a new lib or the first item, start a new batch
        if _libs[i] != current_lib or i == 0:
            # Send the previous batch if not the first iteration
            if i > 0 and len(config_params) > 0:
                extcall ENDPOINT.setConfig(self, current_lib, config_params)

            current_lib = _libs[i]
            config_params = [config_param]
        else:
            # Add to current batch
            config_params.append(config_param)
        # Send the final batch if any params are left


    if len(config_params) > 0:
        extcall ENDPOINT.setConfig(self, current_lib, config_params)


################################################################
#                     GENERIC CONFIG FUNCTION                  #
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
