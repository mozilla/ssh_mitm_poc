#!/usr/bin/env python

# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import base64
from binascii import hexlify
import os
import socket
import sys
import threading
import traceback

import paramiko
from paramiko.py3compat import b, u, decodebytes


# setup logging
paramiko.util.log_to_file('demo_server.log')

host_key = paramiko.RSAKey(filename='host.key')
#host_key = paramiko.DSSKey(filename='test_dss.key')

print('Read key: ' + u(hexlify(host_key.get_fingerprint())))


class Server (paramiko.ServerInterface):
    # 'data' is the output of base64.b64encode(key)
    # (using the "user_rsa_key" files)
    data =    (b'AAAAB3NzaC1yc2EAAAADAQABAAACAQDQzL0E/aSxNtAhx6Jsn5Q9hkTiPnFWxo+gbf9YlPTzc9BxqH/ovatWkWXRhrI+bbMVwVVGJF/wvr0PAZ2HJhrTa6EteL/eyzdO5c4s+cW4jlmfmtb826ylKKVR056S5DfSiWqAcU7qg9m2FNnC6Uaerje3lWkB/MhpP6/+6/s2ytnfYu7EGIRz1FLGO+9V+OB3ep3mwUHTFrvji9zSWs5ssOpaxAi6KLCBgKvHsuOQ00KezRJORv7xTPmFnZOk4QISqGmWLPo0KThNCfPCHS7rTMehvywHOuSOVrGDik7xWTS6i6b5KOIJIn0JTMa+RXn+qcgBsMWZRxwJcLDN2fVK7n7bLQYWhSH/4lQpEcbnMVDFI76dUpXt3YMGZ+M8wZ9Tg4xmmABmws1bF8asfUwBvKvrhGJmBSBIQBAbzOT+NM3jEmgmkYUGJofFAimI9OsPp0CO0mc9vz2gw8/b1JAfVt//ZandX4bG0GBSWFMz0QUREOwV2fnJah7MfpG7D5IiiSE33W580Osw3vF9AAh3yjCN/ZIjpkA7SifGiEhL0bCXrCq4UPuOW1/gjed4QiY/OK0EJO8ZS5nKhpis74H3evZePQPX/p/Ju0h9QEFv80MvqI/J0QWuF4jBUYEuXZFPEJdE4t71F/eY2wsI9vwxRxmSzPtYCFOnpx19gV3wVw==')
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self, transport):
        self.event = threading.Event()
        self.transport = transport

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        print("client provided password {}".format(password))
        if (username == 'kang') and (password == 'testfoo'):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print('Auth attempt with key: ' + u(hexlify(key.get_fingerprint())))
        print('At auth time, session id was ', self.transport.session_id)
        if (username == 'kang') and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password,publickey'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth,
                                  pixelheight, modes):
        return True

class Transport(paramiko.Transport):
    def __init__(self, server):
        super().__init__(server)

# now connect
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 2200))
except Exception as e:
    print('*** Bind failed: ' + str(e))
    traceback.print_exc()
    sys.exit(1)

try:
    sock.listen(100)
    print('Listening for connection ...')
    client, addr = sock.accept()
except Exception as e:
    print('*** Listen/accept failed: ' + str(e))
    traceback.print_exc()
    sys.exit(1)

print('Got a connection!')

try:
    t = Transport(client)
    try:
        t.load_server_moduli()
    except:
        print('(Failed to load moduli -- gex will be unsupported.)')
        raise
    t.add_server_key(host_key)
    server = Server(transport=t)
    try:
        t.start_server(server=server)
    except paramiko.SSHException:
        print('*** SSH negotiation failed.')
        sys.exit(1)

    # wait for auth
    chan = t.accept(20)
    if chan is None:
        print('*** No channel.')
        sys.exit(1)
    print('Authenticated!')

    server.event.wait(10)
    if not server.event.is_set():
        print('*** Client never asked for a shell.')
        sys.exit(1)

    chan.send('\r\nlogged in\r\n')
    chan.close()

except Exception as e:
    print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)

