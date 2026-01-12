import os
import shutil
import subprocess
import sys
import tomllib
from hashlib import blake2b
import urllib.request
from urllib.parse import urlparse

class ChecksumError(Exception):
    pass

def distfetch(distfile, distdir="/tmp/distfiles"):
    print(f"distfile {distfile['uri']}", end='')
    name = distfile['name'] if 'name' in distfile else urlparse(distfile['uri']).path.rsplit('/',1)[1]
    print(f" -> {name}", end='')
    try:
        f = open(f"{distdir}/{name}", 'rb')
        print(" (already downloaded)", end='')
        buf = f.read()
        verify_distfile(distfile, buf)
    except FileNotFoundError:
        print(" (fetch)", end='')
        fetch_and_verify(distfile, distdir)
    print(" OK")

def verify_distfile(distfile, buf):
    h = blake2b(digest_size=len(distfile['blake2b'])//2)
    h.update(buf)
    b2sum = h.hexdigest()
    if b2sum != distfile['blake2b'].lower():
        print(f"!!! failed checksum (expected {distfile['blake2b'].lower()}, got {b2sum}) !!!")
        raise ChecksumError

def fetch_and_verify(distfile, distdir):
    name = distfile['name'] if 'name' in distfile else urlparse(distfile['uri']).path.rsplit('/',1)[1]
    req = urllib.request.Request(distfile['uri'])
    req.add_header('User-Agent', 'Adamantite/0.1 (urllib)')
    with urllib.request.urlopen(req) as f:
        buf = f.read()
    verify_distfile(distfile, buf)
    with open(f"{distdir}/{name}", 'wb') as f:
        f.write(buf)

def build_no_sandbox(package, package_name):
    shutil.rmtree(f"/tmp/build/{package_name}", ignore_errors=True)
    os.makedirs(f"/tmp/build/{package_name}")
    os.makedirs(f"/tmp/build/{package_name}/work")
    os.makedirs(f"/tmp/build/{package_name}/out")
    if 'distfiles' in package:
        for distfile in package['distfiles']:
            name = distfile['name'] if 'name' in distfile else urlparse(distfile['uri']).path.rsplit('/',1)[1]
            shutil.copy(f"/tmp/distfiles/{name}", f"/tmp/build/{package_name}/work")
    with open(f"/tmp/build/{package_name}/build", 'w') as f:
        print(package['build'], file=f)
    build_env = dict(os.environ)
    build_env["PACKAGE_OUT"] = f"/tmp/build/{package_name}/out"
    subprocess.run(["bash", "-e", f"/tmp/build/{package_name}/build"], cwd=f"/tmp/build/{package_name}/work", env=build_env, check=True)
    subprocess.run(["tar", "cf", f"{package_name}_{package['version']}.tar", "-C", f"/tmp/build/{package_name}/out", "."], check=True)

def main():
    package_name = sys.argv[1]
    package = tomllib.load(open(f"{package_name}.toml", 'rb'))
    if 'distfiles' in package:
        os.makedirs("/tmp/distfiles", exist_ok=True)
        for distfile in package['distfiles']:
            distfetch(distfile)
    build_no_sandbox(package, package_name)

if __name__ == '__main__':
    main()
