# LayerZero V2 OApp Vyper Module

This module rewrites all the important LayerZero V2 endpoint interfaces in Vyper into a standalone package. It’s built for anyone looking to integrate cross-chain messaging into their projects with ease and security. Curve Blockash Oracle is powered by this module (GitHub link coming soon).


## Overview

The module simplifies:
- Message encoding and fee estimation.
- Secure transmission and receipt of cross-chain messages.
- Easy integration into your Vyper contracts.

## Security

Always ensure proper peer setup and ownership management when deploying. Code has not been audited yet and probably contains bugs.

## Development

Requirements:
- Python 3.9+
- Vyper 0.4.2
- LayerZero V2 endpoint deployment on your chain of choice

Testing:
```bash
# Setup virtual environment
uv venv
uv sync
source venv/bin/activate

# Run all tests
pytest tests/
```

## Testnet Example

The `lz_testnet.ipynb` notebook included in the repository shows how to deploy this module on a testnet, quote fees, and enable cross-chain message passing. It’s a simple way to see everything in action before integrating into your main project.

Notably, handling incoming messages can follow a recursive pattern. For example, your `lzReceive` might decode a message and trigger another lzSend.

Happy coding!

## Example Use
OAppExample.vy contract provides a simple example of how to use the module.
