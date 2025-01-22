def test_default_behavior(lz_module_contract):
    assert lz_module_contract.allowInitializePath((0, b"0", 0))  # returns true
