"""Public wire-contract test for the package-local Stim ``.b8`` codec."""

from __future__ import annotations

import numpy as np

from error_coupling_simulator.frontend import b8_io


def test_b8_round_trip_preserves_shape_dtype_little_endian_order_and_shot_metadata(
    tmp_path,
) -> None:
    """Ten-bit shots are LSB-first, byte-padded, and recover their declared shape."""

    bits = np.array(
        [
            [1, 0, 1, 0, 0, 0, 0, 1, 1, 0],
            [0, 1, 0, 1, 1, 1, 1, 0, 0, 1],
        ],
        dtype=np.uint8,
    )

    packed = b8_io.pack_bits(bits)
    assert packed.dtype == np.uint8
    assert packed.shape == (2, 2)
    assert packed.tolist() == [[0x85, 0x01], [0x7A, 0x02]]

    path = tmp_path / "records.b8"
    path.write_bytes(np.ascontiguousarray(packed).tobytes())
    assert b8_io.packed_bytes_per_shot(10) == 2
    assert b8_io.num_shots_in_file(path, 10) == 2

    loaded = b8_io.read_b8(path, 10)
    assert loaded.dtype == np.uint8
    assert loaded.shape == (2, 2)
    assert np.array_equal(loaded, packed)

    unpacked = b8_io.unpack_bits(loaded, 10)
    assert unpacked.dtype == np.bool_
    assert unpacked.shape == (2, 10)
    assert np.array_equal(unpacked, bits.astype(np.bool_))
