from grimmealie.cli import mask, stamp, REGION_MAP


def test_mask_short():
    assert mask("hi") == "********"


def test_mask_long():
    assert mask("abcdefgh") == "********"


def test_mask_very_long():
    result = mask("this-is-a-very-long-key-12345")
    assert len(result) == len("this-is-a-very-long-key-12345")


def test_stamp_format():
    s = stamp()
    assert len(s) == 9  # HHMMSSsss


def test_region_map():
    assert REGION_MAP["f"] == "full"
    assert REGION_MAP["t"] == "top"
    assert REGION_MAP["b"] == "bottom"
    assert REGION_MAP["l"] == "left"
    assert REGION_MAP["r"] == "right"
    assert len(REGION_MAP) == 5
