# LayerZero V2 Vyper Module

A Vyper module for LayerZero V2 cross-chain messaging with example implementation.

## Overview

This repository contains:
- `LZv2Module.vy`: Base module for LayerZero V2 messaging
- `ExampleMessenger.vy`: Example implementation for string messaging
- Tests for module functionality

## Contracts

### LZv2Module

Base module that handles core LayerZero V2 functionality:
- Message sending with fee management
- Message receiving with security checks
- Peer management
- Gas limit configuration

Key features:
- Adjustable message size (LZ_MESSAGE_SIZE_CAP)
- Security checks for trusted peers
- Fee quoting and payment handling
- Designed for module imports

### Example Messenger

Example implementation showing how to use the LZ module:
- String message sending across chains
- Message receiving and conversion
- Ownable management for security
- Gas limit configuration

Features:
- String messages up to 128 bytes
- Owner-controlled peer management
- Event emission for tracking
- Example of proper module initialization

## Testing

Tests cover:
1. Message Sending
   - Fee quoting
   - Peer management
   - Event emission

2. Message Receiving
   - Security checks
   - Message conversion
   - Event verification

3. Security
   - Endpoint verification
   - Peer validation
   - Owner controls

## Usage

### Module Import

```python
import LZV2Module as lz
initializes: lz
exports: (
    lz.LZ_ENDPOINT,
    lz.LZ_PEERS,
    lz.LZ_MESSAGE_SIZE_CAP,
    lz.default_gas_limit,
    lz.quote_lz_fee,
)
```

### Initialization

```python
@deploy
def __init__(_endpoint: address, _gas_limit: uint256):
    lz.__init__(_endpoint, _gas_limit)
```

### Sending Messages

```python
@payable
@external
def send_message(_dst_eid: uint32, _receiver: address, _message: String[128]):
    encoded: Bytes[lz.LZ_MESSAGE_SIZE_CAP] = convert(_message, Bytes[lz.LZ_MESSAGE_SIZE_CAP])
    lz._send_message(_dst_eid, _receiver, encoded)
```

### Receiving Messages

```python
@payable
@external
def lzReceive(_origin: lz.Origin, _message: Bytes[lz.LZ_MESSAGE_SIZE_CAP], ...):
    assert lz._lz_receive(...)
    message: String[128] = convert(_message, String[128])
```

## Development

Requirements:
- Python 3.9+
- Vyper ~=0.4
- LayerZero V2 endpoint deployment

Testing:
```bash
# Setup virtual environment
uv venv
uv sync
source venv/bin/activate

# Run all tests
pytest tests/
```

## Security

Always ensure proper peer setup and ownership management when deploying. Code has not been audited yet and probably contains bugs.
