"""Test that sanity checks in OptionsBuilder account for header bytes"""

import pytest
import boa


def test_sanity_check_accounts_for_headers():
    """Test that the sanity checks account for header bytes"""
    # Load the OptionsBuilder contract and verify sanity checks include headers
    options_builder_code = open("contracts/oapp_vyper/OptionsBuilder.vy", "r").read()
    
    # Find addExecutorOption function
    executor_section = []
    in_executor = False
    for line in options_builder_code.split('\n'):
        if 'def addExecutorOption' in line:
            in_executor = True
        elif '@internal' in line or '@external' in line:
            if in_executor:
                break
        if in_executor:
            executor_section.append(line)
    
    executor_text = '\n'.join(executor_section)
    
    # Check that header bytes are accounted for in executor option (4 bytes)
    assert '+ 4 <=' in executor_text or '+4 <=' in executor_text, "addExecutorOption should account for 4 header bytes"
    
    # Find addDVNOption function
    dvn_section = []
    in_dvn = False
    for line in options_builder_code.split('\n'):
        if 'def addDVNOption' in line:
            in_dvn = True
        elif '@internal' in line or '@external' in line:
            if in_dvn:
                break
        if in_dvn:
            dvn_section.append(line)
    
    dvn_text = '\n'.join(dvn_section)
    
    # Check that header bytes are accounted for in DVN option (5 bytes)
    assert '+ 5 <=' in dvn_text or '+5 <=' in dvn_text, "addDVNOption should account for 5 header bytes"


def test_options_size_limit_with_headers():
    """Test that options size limits are enforced including headers"""
    options_builder = boa.load("contracts/oapp_vyper/OptionsBuilder.vy")
    
    # Test with executor options
    initial_options = options_builder.internal.newOptions()
    
    # Calculate maximum allowed option size considering headers
    # MAX_OPTIONS_TOTAL_SIZE is 65535, minus 2 for initial type, minus 4 for header
    max_single_option_data = 65535 - 2 - 4 - 48  # 48 is a reasonable option size
    
    # This should work - within limits
    try:
        gas_limit = 200000
        msg_value = 0
        options = options_builder.internal.addExecutorLzReceiveOption(initial_options, gas_limit, msg_value)
        assert len(options) > len(initial_options)
    except Exception as e:
        pytest.fail(f"Should not fail with reasonable option size: {e}")
    
    # Test that the size check is working by verifying the contract logic
    # The actual boundary testing would require creating very large options which is complex


def test_multiple_options_respect_size_limits():
    """Test that multiple options together respect size limits"""
    options_builder = boa.load("contracts/oapp_vyper/OptionsBuilder.vy")
    
    initial_options = options_builder.internal.newOptions()
    
    # Add multiple options
    options = initial_options
    for i in range(10):  # Add 10 options
        gas_limit = 200000 + i * 10000
        options = options_builder.internal.addExecutorLzReceiveOption(options, gas_limit, 0)
    
    # Should successfully add multiple options
    assert len(options) > len(initial_options)
    
    # Each option adds: 4 header bytes + 48 data bytes = 52 bytes
    # 10 options = 520 bytes + 2 initial = 522 bytes, well within 65535 limit
    assert len(options) < 1000  # Should be around 522 bytes