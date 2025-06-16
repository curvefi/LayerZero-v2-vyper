"""Test safe casting in OptionsBuilder"""

import pytest
import boa


def test_safe_cast_in_executor_option():
    """Test that addExecutorOption uses safe convert() instead of abi_decode/encode"""
    # Load the OptionsBuilder contract and verify it uses convert()
    options_builder_code = open("contracts/oapp_vyper/OptionsBuilder.vy", "r").read()
    
    # Check that convert() is used consistently in both functions
    add_executor_section = []
    add_dvn_section = []
    in_executor = False
    in_dvn = False
    
    for line in options_builder_code.split('\n'):
        if 'def addExecutorOption' in line:
            in_executor = True
            in_dvn = False
        elif 'def addDVNOption' in line:
            in_dvn = True
            in_executor = False
        elif '@internal' in line or '@external' in line:
            in_executor = False
            in_dvn = False
            
        if in_executor:
            add_executor_section.append(line)
        if in_dvn:
            add_dvn_section.append(line)
    
    # Check that abi_decode/encode pattern is NOT used in addExecutorOption
    executor_text = '\n'.join(add_executor_section)
    assert 'abi_decode' not in executor_text, "addExecutorOption should not use abi_decode"
    assert 'abi_encode' not in executor_text, "addExecutorOption should not use abi_encode"
    
    # Check that convert() IS used for downcasting
    assert 'convert(_options, Bytes[' in executor_text, "addExecutorOption should use convert() for downcasting"
    
    # Verify both functions use the same pattern
    dvn_text = '\n'.join(add_dvn_section)
    assert 'convert(_options, Bytes[' in dvn_text, "addDVNOption uses convert() for downcasting"


def test_executor_option_functionality():
    """Test that the fixed addExecutorOption works correctly"""
    options_builder = boa.load("contracts/oapp_vyper/OptionsBuilder.vy")
    
    # Test adding executor option
    initial_options = options_builder.internal.newOptions()
    
    # Add an executor lzReceive option
    gas_limit = 200000
    msg_value = 0
    updated_options = options_builder.internal.addExecutorLzReceiveOption(initial_options, gas_limit, msg_value)
    
    # Verify the option was added correctly
    assert len(updated_options) > len(initial_options)
    
    # Test with multiple options to ensure downcasting works
    second_update = options_builder.internal.addExecutorLzReceiveOption(updated_options, gas_limit * 2, msg_value)
    assert len(second_update) > len(updated_options)
    
    # Test that size limits are enforced
    # This would require creating a very large option, which is complex to test here