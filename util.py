import re
import subprocess
import sys
import os
import os.path
import time

def error(*args):
    print("hc:", *args, file=sys.stderr)

def is_size_str(size_str):
    suffixes = ['KB', 'MB', 'GB', 'TB']
    "+[KMGT]?B"
    pattern = re.compile(r"\d+[KMGT]?B")
    return pattern.match(size_str) is not None

def is_number(char):
    try:
        int(char)
    except ValueError:
        return False
    else:
        return True

# Parses a string like 100MB
def size_to_bytesize(size_str):
    assert is_size_str(size_str)
    assert size_str[-1] == "B"
    multiplier = size_str[-2]
    if is_number(multiplier):
        multiplier = None
        size_str = size_str[:-1]
    else:
        size_str = size_str[:-2]
    bytesize = int(size_str)
    if multiplier == "T":
        bytesize *= 1000 * 1000 * 1000 * 1000
    elif multiplier == "G":
        bytesize *= 1000 * 1000 * 1000
    elif multiplier == "M":
        bytesize *= 1000 * 1000
    elif multiplier == "K":
        bytesize *= 1000
    return bytesize

def create_blank_file(filename, bytesize):
    count = int(bytesize / 1024) + 1
    rc = subprocess.call(["dd", "if=/dev/zero", "of=%s" % filename,
                          "bs=1024", "count=%s" % count])
    return rc == 0

def setup_volume(password, offset, size, slab_filename, options, is_fake):
    mapping_name = options["mapping_name"]
    mapped_device = os.path.join(options["mapping_path"], mapping_name)

    # Setup loop device
    pipe = subprocess.Popen(["losetup", "--offset", str(offset),
                             "--sizelimit", str(size), "--find", "--show",
                             slab_filename],
                            stdout=subprocess.PIPE)
    loop_device = pipe.communicate()[0][:-1].decode()
    if pipe.returncode:
        error("Problem mounting loop device.")
        return pipe.returncode
    print("Using loop device:", loop_device)

    # Format the volume
    pipe = subprocess.Popen(["cryptsetup", "-q", "luksFormat", loop_device],
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    out = pipe.communicate(input=password)
    if pipe.returncode:
        error("Problem formatting volume.")
        return pipe.returncode

    # Open the volume
    pipe = subprocess.Popen(["cryptsetup", "-q", "luksOpen",
                            loop_device, mapping_name],
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    pipe.communicate(input=password)
    if pipe.returncode:
        error("Problem opening volume.")
        return pipe.returncode

    # Zero the data.
    pipe = subprocess.Popen(["dd", "if=/dev/zero", "of=%s" % mapped_device],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pipe.communicate()
    # Ignore rc 1 because that's normal.
    if pipe.returncode and pipe.returncode != 1:
        error("Problem zeroing volume.")
        return pipe.returncode

    # Format the volume.
    rc = subprocess.call(["mkfs.ext4", mapped_device])
    if rc:
        error("Problem formatting volume.")
        return rc

    time.sleep(2)
    subprocess.call(["cryptsetup", "luksClose", mapping_name])
    subprocess.call(["losetup", "-d", loop_device])

    if is_fake:
        print("FAKE ENCRYPTED VOLUME CREATED")
    else:
        print("****************************")
        print("NEW ENCRYPTED VOLUME CREATED")
        print("****************************")
        print()
        print("Now run: sudo hc open")
    return 0

def mount_volume(password, offset, size, slab_filename, options):
    # Close previously opened volumes.
    close_volume(options)

    mapping_name = options["mapping_name"]
    mapped_device = os.path.join(options["mapping_path"], mapping_name)

    # Setup loop device
    pipe = subprocess.Popen(["losetup", "--offset", str(offset),
                             "--sizelimit", str(size), "--find", "--show",
                             slab_filename],
                            stdout=subprocess.PIPE)
    loop_device = pipe.communicate()[0][:-1].decode()
    if pipe.returncode:
        error("Problem mounting loop device.")
        return pipe.returncode
    print("Using loop device:", loop_device)

    # Open the volume
    pipe = subprocess.Popen(["cryptsetup", "-q", "luksOpen",
                            loop_device, mapping_name],
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    pipe.communicate(input=password)
    if pipe.returncode:
        error("Problem opening volume.")
        return pipe.returncode

    # Mount the volume
    rc = subprocess.call(["mount", mapped_device, options["mount_path"]])
    if rc:
        error("Unable to mount volume.")
        return rc

    print("************************")
    print("ENCRYPTED VOLUME MOUNTED")
    print("************************")
    return 0

def find_loop_device(mapping_name):
    pipe = subprocess.Popen(["cryptsetup", "status", mapping_name],
                            stdout=subprocess.PIPE)
    output, errs = pipe.communicate()
    line = [line for line in output.decode().split("\n") if "device" in line]
    if not line:
        return None
    assert len(line) == 1
    line = line[0]
    loop_device = line.split(":")[1].strip()
    return loop_device

def close_volume(options):
    rc = subprocess.call(["umount", options["mount_path"]])
    if rc:
        return 0

    mapping_name = options["mapping_name"]

    loop_device = find_loop_device(mapping_name)

    subprocess.call(["cryptsetup", "luksClose", mapping_name])

    if loop_device is None:
        return 0
    # umount foo bar
    subprocess.call(["losetup", "-d", loop_device])
    return 0

