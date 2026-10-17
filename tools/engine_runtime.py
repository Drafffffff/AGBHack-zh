#!/usr/bin/env python3
"""Run a ROM with a caller-provided mGBA libretro core and save menu frames.

No access to OpenEmu's saves/configuration. Each run starts with blank SRAM.
Dependencies: Python Pillow, compiled mGBA libretro shared library.
"""
import argparse
import ctypes as C
import json,hashlib,zlib
from pathlib import Path

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--scenario",choices=["menu","game","tutorial"],default="menu")
    ap.add_argument("--trace",action="store_true",help="Capture every unique transition frame, including intermediate frames")
    args = ap.parse_args()
    core = C.CDLL(str(args.core.resolve()))
    args.out.mkdir(parents=True, exist_ok=True)
    state = {"keys": set(), "image": None, "format": 2}
    ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
    POLL = C.CFUNCTYPE(None)
    INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

    @ENV
    def env(cmd, data):
        if cmd == 10:  # SET_PIXEL_FORMAT
            state["format"] = C.cast(data, C.POINTER(C.c_int)).contents.value
            return state["format"] == 2
        if cmd == 17:  # GET_VARIABLE_UPDATE
            C.cast(data, C.POINTER(C.c_bool)).contents.value = False
            return True
        return False

    trace=[];seen=set();frame=0
    @VIDEO
    def video(ptr,width,height,pitch):
        nonlocal frame
        frame+=1
        if not ptr or (not args.trace and not state.get("capture",False)):return
        raw=C.string_at(ptr,pitch*height)
        # Decode RGB565 in native Pillow code, including the core's padded stride.
        im=Image.frombytes("RGB",(width,height),raw,"raw","BGR;16",pitch)
        if state.get("capture",False):state["image"]=im
        if args.trace:
            crc=f"{zlib.crc32(im.tobytes()):08x}"
            box=im.getextrema();blank=all(a==b for a,b in box)
            trace.append({"frame":frame,"hash":crc,"uniform":blank,"keys":sorted(state["keys"])})
            if crc not in seen:
                seen.add(crc);d=args.out/"frames";d.mkdir(exist_ok=True)
                im.save(d/(crc+".png"))

    audio = AUDIO(lambda left, right: None)
    batch = BATCH(lambda ptr, frames: frames)
    poll = POLL(lambda: None)
    input_cb = INPUT(lambda port, device, index, key: int(key in state["keys"]))
    for name, callback in [("environment", env), ("video_refresh", video),
                           ("audio_sample", audio), ("audio_sample_batch", batch),
                           ("input_poll", poll), ("input_state", input_cb)]:
        getattr(core, "retro_set_" + name).argtypes = [type(callback)]
        getattr(core, "retro_set_" + name)(callback)
    core.retro_init()

    class Game(C.Structure):
        _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                    ("size", C.c_size_t), ("meta", C.c_char_p)]

    rom_bytes = args.rom.read_bytes()
    rom_data = C.create_string_buffer(rom_bytes)
    game = Game(str(args.rom.resolve()).encode(), C.cast(rom_data, C.c_void_p), len(rom_bytes), None)
    core.retro_load_game.argtypes = [C.POINTER(Game)]
    core.retro_load_game.restype = C.c_bool
    if not core.retro_load_game(C.byref(game)):
        raise SystemExit("Could not load ROM")

    def run(frames, keys=()):
        state["keys"] = set(keys)
        for i in range(frames):
            state["capture"]=i==frames-1
            core.retro_run()

    def save(name):
        if state["image"] is None:
            raise RuntimeError("No video output")
        state["image"].save(args.out / (name + ".png"))
        state["image"].resize((720, 480), Image.Resampling.NEAREST).save(args.out / (name + "_3x.png"))

    run(300)
    save("boot")

    core.retro_unload_game()
    core.retro_deinit()

if __name__ == "__main__": main()
