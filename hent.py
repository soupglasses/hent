#!/usr/bin/env python3

import argparse
from itertools import zip_longest
import platform
import subprocess
import os

DISTROS_ART = {
    'arch': r"""        ..
        cc
       :ooc
      ::lool
    .looooool.
   .loo;..;ooo.
  'oooo    looc.
 ;l;'..     .';l;
..              .'
""",
    'debian': r"""     ,c;;'
  'odl,'',cdl.
.o:.        :k.
x.    ..     x.
x    '.      o
x     ''.....
.x.
  c,
    '..
""",
    'fedora': r"""      ......
   .....'cdxx;.
 ......:NNxll::,.
.......kMo...':;..
..',cO0NMX0O::;'..
.;:,';:OMx:;''....
.::'..'KMc.......
.';dXXWKl......
 ...',......
""",
    'void': r"""     ..',;;,'..
     .,'....';;;'.
 ,c.          .,;;.
.oo:   .',,'.   ';;.
,oo.   ;;;;;;   .;;.
.oo:    ',,'    ';;.
 ,oo:.          .,.
  .;lol;,'',;:.
     .,;:cc:;,.
""",
    'gentoo': r"""    ,:ccl:
  .,,...'..;;,
';....kxlx;..:c.
 cll;..:;:.....oc
   .o:........lk'
 ';'.......;dx;
o'......cddc.
,dlllllc'
  ....
""",
    'linux': r"""     cOKxc
    .0K0kWc
    .x,':Nd
   .l... ,Wk.
  .0.     ,NN,
 .K;       0N0
..'cl.    'xO:
,''';c'':Oc',,.
  ..'.  ..,,.
""",
}

DISTROS_COLOR = {
    'arch': '\x1b[34m',
    'debian': '\x1b[31m',
    'fedora': '\x1b[34m',
    'void': '\x1b[32m',
    'gentoo': '\x1b[35m',
    'linux': '\x1b[33m',
}

CPU_BLACKLIST = [
    'Intel(R) Core(TM)',
    'CPU',
    '6-Core Processor',
    '8-Core Processor',
    '12-Core Processor',
]

PKGS = {
    'pacman': ['pacman', '-Qq'],
    'rpm': ['rpm', '-qa'],
    'dpkg': ['dpkg', '--list'],
    'flatpak': ['flatpak', 'list'],
    'snap': ['snap', 'list'],
}


def os_release() -> dict:
    with open('/etc/os-release') as f:
        return dict(line.replace('"', '').split('=', 1)
                    for line in f.read().splitlines())


def distro():
    return f"{os_release()['NAME']} {platform.machine()}"


def uptime():
    cmd = subprocess.run(['uptime', '--pretty'], capture_output=True)
    return cmd.stdout.decode('ascii')[3:-1]


def count_pkgs():
    output = {}
    for manager, command in PKGS.items():
        try:
            cmd = subprocess.run(command, capture_output=True)
            output[manager] = cmd.stdout.decode('ascii').count('\n')
        except FileNotFoundError:
            pass
    return ', '.join(f"{count} ({manager})"
                     for manager, count in output.items())


def shell():
    return os.environ['SHELL'].split('/')[-1]


def cpu_info():
    with open('/proc/cpuinfo') as f:
        cpu = next(line for line in f if line.startswith('model name'))
    cpu = cpu.split(':', 1)[1][1:-1]

    for bad_word in CPU_BLACKLIST:
        cpu = cpu.replace(bad_word, '')
    cpu = ' '.join(word for word in cpu.split(' ') if word)

    return cpu


def ram():
    with open('/proc/meminfo') as f:
        meminfo = dict(line.replace(' ', '').split(':')
                       for line in f.read().splitlines()[:5])
        meminfo = {key: int(val[:-2])
                   for key, val in meminfo.items()}

        free = meminfo['MemFree']
        total = meminfo['MemTotal']
        total_used = total - free

        cache = meminfo['Cached']
        buffers = meminfo['Buffers']
        used = total_used - (cache + buffers)

        return f"{int(used/1024)}MB / {int(total/1024)}MB"


def gpu():
    cmd = subprocess.run(['lspci'], capture_output=True)
    stdout = cmd.stdout.decode('ascii')

    for line in stdout.splitlines():
        if 'VGA' in line:
            if '[' in line:
                return line[line.rfind('[') + 1:line.rfind(']')]
            else:
                return line.split('VGA compatible controller: ')[1]


def term():
    return os.environ['TERM']


data = {
    'Distro': distro(),
    'Kernel': platform.release(),
    'Uptime': uptime(),
    'Packages': count_pkgs(),
    'Shell': shell(),
    'Terminal': term(),
    'CPU': cpu_info(),
    'GPU': gpu(),
    'Memory': ram(),
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Neofetch inspired fetch tool built in python.'
    )
    parser.add_argument('--distro', choices=DISTROS_ART,
                        metavar='distro',
                        help='which ascii art to use')
    parser.add_argument('--color', choices=['true', 'false'],
                        metavar='true/false',
                        help='enable/disable colored output')

    args = parser.parse_args()
    if args.distro:
        distro = args.distro
    else:
        distro = os_release()['ID']

    if distro in DISTROS_ART:
        art = DISTROS_ART[distro].splitlines()
        color = DISTROS_COLOR[distro]
    else:
        art = DISTROS_ART['linux'].splitlines()
        color = DISTROS_COLOR['linux']

    reset = '\x1b[0m'

    if args.color == 'no':
        color, reset = '', ''

    text_max_len = len(max(data)) + 2
    art_max_len = max(len(line) for line in art) + 1

    for art_line, (key, val) in zip_longest(art, data.items(), fillvalue=''):
        print(f'{color} {art_line.ljust(art_max_len, " ")} {reset}',
              f'{color}{key.rjust(text_max_len, " ")}:{reset}',
              val)
