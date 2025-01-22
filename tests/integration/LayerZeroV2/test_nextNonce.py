def test_default_behavior(lz_module_contract):
    assert lz_module_contract.nextNonce(0, b"0") == 0
