from math import ceil, sqrt
from nand.bit_packed_encoder import BitPackedEncoder
from nand.default_encoder import DefaultEncoder
from nand.nand2tetris_hack_alu import HackALUBuilder

builder = HackALUBuilder()
builder.build_circuits()
library = builder.library

default_encoded = DefaultEncoder().encode(library)
bit_packed_encoded = BitPackedEncoder().encode(library)

import zlib

bp_zip = zlib.compress(bit_packed_encoded.tobytes(), level=9, wbits=-15)
de_zip = zlib.compress(default_encoded.tobytes(), level=9, wbits=-15)
print(f"bp sz = {len(bit_packed_encoded.tobytes())}")
print(f"bp zip sz = {len(bp_zip)}")

# import gzip
#
# bp_gzip = gzip.compress(bit_packed_encoded.tobytes(), compresslevel=9)
# de_gzip = gzip.compress(default_encoded.tobytes(), compresslevel=9)
#
# import bz2
#
# bp_bzip2 = bz2.compress(bit_packed_encoded.tobytes(), compresslevel=9)
# de_bzip2 = bz2.compress(default_encoded.tobytes(), compresslevel=9)

import lzma


filters = [
    {
        "id": lzma.FILTER_LZMA2,
        "dict_size": 1
        << 26,  # 64 MiB dictionary (increase if memory allows, e.g. 1<<27 for 128 MiB)
        "lc": 3,  # default literal context bits
        "lp": 0,
        "pb": 2,
        "mode": lzma.MODE_NORMAL,
        "nice_len": 273,  # maximum
        "mf": lzma.MF_BT4,  # strongest match finder
        "depth": 0,  # auto
    }
]

bp_lzma = lzma.compress(
    bit_packed_encoded.tobytes(),
    format=lzma.FORMAT_RAW,
    filters=filters,
)
de_lzma = lzma.compress(
    default_encoded.tobytes(),
    format=lzma.FORMAT_RAW,
    filters=filters,
)

print(f"bp lzma sz = {len(bp_lzma)}")

from PIL import Image
import numpy as np

# Using a more standard gray checkerboard, but you can change the colors
CHECKER_COLOR_1 = (128, 128, 128, 255)  # Medium gray
CHECKER_COLOR_2 = (192, 192, 192, 255)  # Light gray
RESAMPLE_NEAREST = Image.Resampling.NEAREST


def _apply_checkerboard(img, box_size=5):
    """
    Applies a checkerboard background to an RGBA image.
    This is a more efficient, vectorized version.
    """
    # Ensure the image to be composited has an alpha channel
    img = img.convert("RGBA")
    w, h = img.size

    # Create the checkerboard pattern with NumPy
    # Create arrays of indices
    x_idx = np.arange(w)
    y_idx = np.arange(h)

    # Calculate the checker pattern using broadcasting
    # (y_idx[:, None] // box_size) creates a column vector
    # (x_idx[None, :] // box_size) creates a row vector
    # Adding them broadcasts to a 2D grid
    checker_pattern = ((y_idx[:, None] // box_size) + (x_idx[None, :] // box_size)) % 2

    # Create an empty RGBA background array
    bg_arr = np.zeros((h, w, 4), dtype=np.uint8)

    # Use boolean indexing to set the colors
    bg_arr[checker_pattern == 0] = CHECKER_COLOR_1
    bg_arr[checker_pattern == 1] = CHECKER_COLOR_2

    bg = Image.fromarray(bg_arr, "RGBA")

    # Composite the original image over the checkerboard background
    return Image.alpha_composite(bg, img)


def visualize_as_image(
    data: bytes,
    mode="gray",
    width=256,
    scale=4,
    save_path=None,
    transparent=True,
    background="transparent",
) -> Image.Image:
    """
    Visualize binary data as an image.

    Parameters:
        data (bytes): raw binary data
        mode (str): "gray" (0-255), "bw" (1-bit), or "rgb"
        width (int): image width in pixels
        scale (int): factor to scale the image for visibility
        save_path (str|None): optional path to save the image (e.g. "out.png")
        transparent (bool): if True, pad with transparency instead of truncating
        background (str): "transparent", "checker", "black", "white"

    Returns:
        PIL.Image.Image object
    """

    # --- create the base image ---
    if mode == "gray":
        data_len = len(data)  # <<< FIX: Store original data length
        arr_1d = np.frombuffer(data, dtype=np.uint8)
        height = -(-data_len // width)  # ceil division

        padded_1d = np.zeros((height * width,), dtype=np.uint8)
        padded_1d[:data_len] = arr_1d
        pixel_arr = padded_1d.reshape((height, width))

        if transparent:
            alpha = np.full_like(pixel_arr, 255, dtype=np.uint8)
            alpha.flat[data_len:] = 0  # <<< FIX: Use original length for slicing
            img = Image.fromarray(np.dstack([pixel_arr, alpha]), mode="LA")
        else:
            img = Image.fromarray(pixel_arr, mode="L")

    elif mode == "bw":
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        bits_len = len(bits)  # This part was already correct
        height = -(-bits_len // width)

        padded = np.zeros((height * width,), dtype=np.uint8)
        padded[:bits_len] = bits
        pixel_arr = padded.reshape((height, width)) * 255

        if transparent:
            alpha = np.full_like(pixel_arr, 255, dtype=np.uint8)
            alpha.flat[bits_len:] = 0
            img = Image.fromarray(np.dstack([pixel_arr, alpha]), mode="LA")
        else:
            img = Image.fromarray(pixel_arr, mode="L")

    elif mode == "rgb":
        data_len = len(data)  # <<< FIX: Store original data length
        arr_1d = np.frombuffer(data, dtype=np.uint8)

        # Calculate pixels based on original data to handle padding correctly
        num_pixels = -(-data_len // 3)
        height = -(-num_pixels // width)

        # Pad the RGB data
        padded_1d = np.zeros((height * width * 3,), dtype=np.uint8)
        padded_1d[:data_len] = arr_1d
        pixel_arr = padded_1d.reshape((height, width, 3))

        if transparent:
            # Create alpha channel based on pixel count, not byte count
            alpha_1d = np.full((height * width,), 255, dtype=np.uint8)
            alpha_1d[num_pixels:] = 0  # <<< FIX: Use pixel count to set transparency
            alpha_2d = alpha_1d.reshape((height, width, 1))

            img = Image.fromarray(
                np.concatenate([pixel_arr, alpha_2d], axis=2), mode="RGBA"
            )
        else:
            img = Image.fromarray(pixel_arr, mode="RGB")

    else:
        raise ValueError("mode must be 'gray', 'bw', or 'rgb'")

    # --- scale up ---
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), RESAMPLE_NEAREST)

    # --- apply background ---
    if background != "transparent" and img.mode in ("LA", "RGBA"):
        # Convert to RGBA if needed (for LA mode)
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        if background == "checker":
            img = _apply_checkerboard(img)
        elif background == "black":
            bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
            img = Image.alpha_composite(bg, img)
        elif background == "white":
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            img = Image.alpha_composite(bg, img)
        else:
            raise ValueError(
                "background must be 'transparent', 'checker', 'black', or 'white'"
            )

    # --- save if requested ---
    if save_path:
        img.save(save_path)

    return img


width = ceil(sqrt(len(bit_packed_encoded.tobytes() * 8)))
scale = 10
transparent = True
visualize_as_image(
    bit_packed_encoded.tobytes(),
    mode="bw",
    width=width,
    scale=scale,
    transparent=transparent,
    background="checker",
    save_path="bp_def_sq.png",
).show("bp_raw")
visualize_as_image(
    bp_lzma,
    mode="bw",
    width=width,
    scale=scale,
    transparent=transparent,
    background="checker",
    save_path="bp_zip_sq.png",
).show("bp zip")
# print(len(bit_packed_encoded.tobytes()))
# print()
# print(len(bp_zip))
