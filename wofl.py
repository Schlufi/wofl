#!/usr/bin/env python
import sys
import subprocess
import multiprocessing

WOFL_VERSION = "1.0"
MIPMAP_NUM = 4


def error_exit(msg):
    print(msg.strip())
    exit(1)


def int_b(n, l=4):
    try:
        return n.to_bytes(l, "little")
    except BaseException:
        error_exit("Overflow exception.")


def run_cmd(cmd, **kwargs):
    proc = subprocess.run(cmd, capture_output=True, **kwargs)

    if proc.stderr:
        error_exit(proc.stderr.decode())

    return proc


def image_info(files):
    proc = run_cmd(["magick", "identify", "-format", "%w %h\n"] + files)

    names, dims = [], []
    div = 2 ** (MIPMAP_NUM - 1)

    for line, cur_file in zip(proc.stdout.decode().splitlines(), files):
        w, h = [int(i) for i in line.split()]
        if w % div or h % div:
            error_exit(
                cur_file +
                " has invalid resolution " +
                str(w) +
                "x" +
                str(h) +
                ".")

        dims.append([w, h])

        try:
            idx = cur_file.rindex('.')
            name = cur_file[:idx]
        except BaseException:
            name = cur_file

        name = bytes(name, encoding="ascii")
        name = name[:min(len(name), 16)]
        names.append(name)

    name_set = set()
    for name in names:
        if name in name_set:
            error_exit("Duplicate texture name '" + name.decode() + "'.")
        name_set.add(name)

    return names, dims


def texture_file(f, name, dim):
    mip_cmd = (["magick", "convert", f, "-write", "RGB:-"]
               + ["-resize", "50%", "-write", "RGB:-"] * (MIPMAP_NUM - 2)
               + ["-resize", "50%", "RGB:-"])
    rgb_img = run_cmd(mip_cmd).stdout
    rgb_size = len(rgb_img) // 3

    h_res = dim[0]
    while rgb_size % h_res:
        h_res //= 2
    v_res = rgb_size // h_res

    map_img = run_cmd(["magick", "convert", "-size", f"{h_res}x{v_res}",
                       "-depth", "8", "RGB:-", "-colors", "256", "+dither",
                       "MAP:-"], input=rgb_img).stdout

    num_colors = (len(map_img) - rgb_size) // 3

    mip_offset = [40 + 2]
    for i in range(0, MIPMAP_NUM - 1):
        mip_offset.append(mip_offset[-1] + dim[0] * dim[1] // 4**i)

    header = name.ljust(16, b'\0') + \
        b''.join([int_b(n) for n in dim + mip_offset])

    return b''.join([header,
                     b'\0' * 2,
                     map_img[3 * num_colors:],
                     b'\0' * 2,
                     map_img[: 3 * num_colors].ljust(256 * 3, bytes([0xff])),
                     b'\0' * 2])


def wad_file(textures):
    texture_offset = [12]
    for tex in textures:
        texture_offset.append(texture_offset[-1] + len(tex))

    header = b"WAD3" + int_b(len(textures)) + int_b(texture_offset[-1])

    entries = []
    for offset, tex in zip(texture_offset, textures):
        entry = [int_b(offset),
                 2 * int_b(len(tex)),
                 bytes([0x43]),
                 3 * b'\0',
                 tex[: 16]]

        entries.append(b''.join(entry))

    return b''.join([header] + textures + entries)


def texture_helper(x):
    return texture_file(*x)


def main():
    if len(sys.argv) < 3:
        print("WADs Out For [The] Ladies v" + WOFL_VERSION)
        print("Usage: wofl input1 [input2 ...] output")
        exit(1)

    output_file = sys.argv[-1]
    input_files = sys.argv[1: -1]
    input_names, input_dims = image_info(input_files)

    def temp(x): return texture_file(*x)
    pool = multiprocessing.Pool()
    texture_files = pool.map(
        texture_helper, zip(
            input_files, input_names, input_dims))

    with open(output_file, "wb") as f:
        f.write(wad_file(texture_files))


if __name__ == "__main__":
    main()
