# pragma version 0.4.1

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
#                           CONSTANTS                          #
################################################################

# Constants for DVN configuration
MAX_DVNS: constant(uint256) = 16

# Config types
CONFIG_TYPE_ULN: constant(uint32) = 0
CONFIG_TYPE_EXECUTOR: constant(uint32) = 1
CONFIG_TYPE_READ: constant(uint32) = 2


################################################################
#                           STRUCTS                            #
################################################################

struct SetConfigParam:
    eid: uint32
    configType: uint32
    config: Bytes[9 * 32 + 2 * MAX_DVNS * 32]  # 9 words for ULNConfig, 2*MAX_DVNS words for DVNs


struct ULNConfig:
    confirmations: uint64
    required_dvn_count: uint8
    optional_dvn_count: uint8
    optional_dvn_threshold: uint8
    required_dvns: DynArray[address, MAX_DVNS]
    optional_dvns: DynArray[address, MAX_DVNS]


struct ULNReadConfig:
    executor: address
    required_dvn_count: uint8
    optional_dvn_count: uint8
    optional_dvn_threshold: uint8
    required_dvns: DynArray[address, MAX_DVNS]
    optional_dvns: DynArray[address, MAX_DVNS]


struct ULNExecutorConfig:
    max_message_size: uint32
    executor: address


################################################################
#                    DVN/ULN CONFIG FUNCTIONS                  #
################################################################

@external
def prepareUlnConfig(
    _lib: address,
    _eid: uint32,
    _confirmations: uint64,
    _optional_dvn_threshold: uint8,
    _required_dvns: DynArray[address, MAX_DVNS],
    _optional_dvns: DynArray[address, MAX_DVNS],
) -> SetConfigParam:
    """
    @notice Prepare a ULN (DVN) configuration
    @param _lib Library address
    @param _eid Endpoint ID
    @param _confirmations Confirmation count
    @param _optional_dvn_threshold Optional DVN threshold
    @param _required_dvns Array of required DVN addresses
    @param _optional_dvns Array of optional DVN addresses
    """

    # Group configurations by lib for batch processing
    current_lib: address = empty(address)
    # Get DVN counts directly from array lengths
    required_count: uint8 = convert(len(_required_dvns), uint8)
    optional_count: uint8 = convert(len(_optional_dvns), uint8)

    # Verify threshold is valid
    assert _optional_dvn_threshold <= optional_count, "OAppConfig: Invalid DVN threshold"

    # Create the ULN config
    uln_config: ULNConfig = ULNConfig(
        confirmations=_confirmations,
        required_dvn_count=required_count,
        optional_dvn_count=optional_count,
        optional_dvn_threshold=_optional_dvn_threshold,
        required_dvns=_required_dvns,
        optional_dvns=_optional_dvns,
    )

    # Create the config parameter
    config_param: SetConfigParam = SetConfigParam(
        eid=_eid, configType=CONFIG_TYPE_ULN, config=abi_encode(uln_config)
    )

    return config_param

@external
def prepareUlnReadConfig(
    _eid: uint32,
    _executor: address,
    _optional_dvn_threshold: uint8,
    _required_dvns: DynArray[address, MAX_DVNS],
    _optional_dvns: DynArray[address, MAX_DVNS],
) -> SetConfigParam:
    """
    @notice Set multiple ULN Read configurations in a single transaction
    @param _eid Endpoint ID
    @param _executor Executor address
    @param _optional_dvn_threshold Optional DVN threshold
    @param _required_dvns Array of required DVN addresses
    @param _optional_dvns Array of optional DVN addresses
    """

    # Get DVN counts directly from array lengths
    required_count: uint8 = convert(len(_required_dvns), uint8)
    optional_count: uint8 = convert(len(_optional_dvns), uint8)

    # Verify threshold is valid
    assert _optional_dvn_threshold <= optional_count, "OAppConfig: Invalid DVN threshold"

    # Create the ULN Read config
    uln_read_config: ULNReadConfig = ULNReadConfig(
        executor=_executor,
        required_dvn_count=required_count,
        optional_dvn_count=optional_count,
        optional_dvn_threshold=_optional_dvn_threshold,
        required_dvns=_required_dvns,
        optional_dvns=_optional_dvns,
    )

    # Create the config parameter
    config_param: SetConfigParam = SetConfigParam(
        eid=_eid, configType=CONFIG_TYPE_READ, config=abi_encode(uln_read_config)
    )

    return config_param


@external
def prepareExecutorConfig(
    _lib: address,
    _eid: uint32,
    _executor: address,
    _max_message_size: uint32,
) -> SetConfigParam:
    """
    @notice Set multiple executor configurations in a single transaction
    @param _lib Library address
    @param _eid Endpoint ID
    @param _executor Executor address
    """
    # Create the Executor config
    executor_config: ULNExecutorConfig = ULNExecutorConfig(
        max_message_size=_max_message_size, executor=_executor
    )

    # Create the config parameter
    config_param: SetConfigParam = SetConfigParam(
        eid=_eid, configType=CONFIG_TYPE_EXECUTOR, config=abi_encode(executor_config)
    )

    return config_param
