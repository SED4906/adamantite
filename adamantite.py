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

def prepare_build_directory(package, package_name):
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
    os.chmod(f"/tmp/build/{package_name}/build", 0o777)

def build_no_sandbox(package, package_name):
    prepare_build_directory(package, package_name)
    build_env = dict(os.environ)
    build_env["PACKAGE_OUT"] = f"/tmp/build/{package_name}/out"
    subprocess.run(["bash", "-e", f"/tmp/build/{package_name}/build"], cwd=f"/tmp/build/{package_name}/work", env=build_env, check=True)
    subprocess.run(["tar", "caf", f"{package_name}_{package['version']}.tar.zst", "-C", f"/tmp/build/{package_name}/out", "."], check=True)

def explicit_dependency(package_name, depend_name):
    depend = tomllib.load(open(f"{depend_name}.toml", 'rb'))
    if not os.path.isfile(f"{depend_name}_{depend['version']}.tar.zst"):
        main(depend_name)
    subprocess.run(["tar", "xf", f"{depend_name}_{depend['version']}.tar.zst", "-C", f"/tmp/build/{package_name}", "--keep-directory-symlink"], check=True)

def implied_dependency(package_name, depend_name):
    depend = tomllib.load(open(f"{depend_name}.toml", 'rb'))
    if not os.path.isfile(f"{depend_name}_{depend['version']}.tar.zst"):
        if 'distfiles' in depend:
            os.makedirs("/tmp/distfiles", exist_ok=True)
            for distfile in depend['distfiles']:
                distfetch(distfile)
        build_no_sandbox(depend, depend_name)
    subprocess.run(["tar", "xf", f"{depend_name}_{depend['version']}.tar.zst", "-C", f"/tmp/build/{package_name}", "--keep-directory-symlink"], check=True)

def build_sandboxed(package, package_name):
    prepare_build_directory(package, package_name)
    os.makedirs(f"/tmp/build/{package_name}/usr/bin")
    os.symlink("bin",f"/tmp/build/{package_name}/usr/sbin")
    os.symlink("usr/bin",f"/tmp/build/{package_name}/bin")
    os.symlink("bin",f"/tmp/build/{package_name}/sbin")
    os.symlink("usr/lib",f"/tmp/build/{package_name}/lib")
    os.symlink("lib",f"/tmp/build/{package_name}/usr/lib64")
    os.symlink("lib",f"/tmp/build/{package_name}/lib64")
    os.makedirs(f"/tmp/build/{package_name}/proc")
    os.makedirs(f"/tmp/build/{package_name}/dev")
    os.makedirs(f"/tmp/build/{package_name}/sys")
    os.makedirs(f"/tmp/build/{package_name}/tmp")
    os.makedirs(f"/tmp/build/{package_name}/run")
    implied_dependency(package_name, 'linux-headers')
    implied_dependency(package_name, 'glibc')
    implied_dependency(package_name, 'ncurses')
    implied_dependency(package_name, 'acl')
    implied_dependency(package_name, 'attr')
    implied_dependency(package_name, 'libcap')
    implied_dependency(package_name, 'readline')
    implied_dependency(package_name, 'zlib')
    implied_dependency(package_name, 'openssl')
    implied_dependency(package_name, 'bash')
    implied_dependency(package_name, 'gmp')
    implied_dependency(package_name, 'mpfr')
    implied_dependency(package_name, 'mpc')
    implied_dependency(package_name, 'gcc')
    implied_dependency(package_name, 'patch')
    implied_dependency(package_name, 'sed')
    implied_dependency(package_name, 'gawk')
    implied_dependency(package_name, 'grep')
    implied_dependency(package_name, 'gzip')
    implied_dependency(package_name, 'bzip2')
    implied_dependency(package_name, 'xz')
    implied_dependency(package_name, 'zstd')
    implied_dependency(package_name, 'tar')
    implied_dependency(package_name, 'make')
    implied_dependency(package_name, 'binutils')
    implied_dependency(package_name, 'coreutils')
    implied_dependency(package_name, 'diffutils')
    implied_dependency(package_name, 'findutils')
    implied_dependency(package_name, 'flex')
    if 'depends' in package:
        for depend_name in package['depends']:
            explicit_dependency(package_name, depend_name)
    subprocess.run(["sudo", "arch-chroot", f"/tmp/build/{package_name}", "/bin/bash", "-e", "-c", f"cd /work;PACKAGE_OUT=/out /build"], check=True)
    subprocess.run(["tar", "caf", f"{package_name}_{package['version']}.tar.zst", "-C", f"/tmp/build/{package_name}/out", "."], check=True)

def main(package_name):
    package = tomllib.load(open(f"{package_name}.toml", 'rb'))
    if 'distfiles' in package:
        os.makedirs("/tmp/distfiles", exist_ok=True)
        for distfile in package['distfiles']:
            distfetch(distfile)
    build_sandboxed(package, package_name)

if __name__ == '__main__':
    main(sys.argv[1])
