#!/usr/bin/env python3.7
#
# Copyright (c) 2013-2024 by Ron Frederick <ronf@timeheart.net> and others.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License v2.0 which accompanies this
# distribution and is available at:
#
#     http://www.eclipse.org/legal/epl-2.0/
#
# This program may also be made available under the following secondary
# licenses when the conditions for such availability set forth in the
# Eclipse Public License v2.0 are satisfied:
#
#    GNU General Public License, Version 2.0, or any later versions of
#    that license
#
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later
#
# Contributors:
#     Ron Frederick - initial implementation, API, and documentation

# To run this program, the file ``ssh_host_key`` must exist with an SSH
# private key in it to use as a server host key. An SSH host certificate
# can optionally be provided in the file ``ssh_host_key-cert.pub``.
#
# The file ``ssh_user_ca`` must exist with a cert-authority entry of
# the certificate authority which can sign valid client certificates.

import asyncio, asyncssh, sys

class MySSHServerSession(asyncssh.SSHServerSession):
    def __init__(self):
        self._input = ''
        self._total = 0

    def connection_made(self, chan: asyncssh.SSHServerChannel):
        self._chan = chan

    def shell_requested(self) -> bool:
        return True

    def session_started(self) -> None:
        self._chan.write('Enter numbers one per line, or EOF when done:\n')

    def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
        self._input += data

        lines = self._input.split('\n')
        for line in lines[:-1]:
            try:
                if line:
                    self._total += int(line)
            except ValueError:
                self._chan.write_stderr(f'Invalid number: {line}\n')

        self._input = lines[-1]

    def eof_received(self) -> bool:
        self._chan.write(f'Total = {self._total}\n')
        self._chan.exit(0)
        return False

    def break_received(self, msec: int) -> bool:
        return self.eof_received()

    def soft_eof_received(self) -> None:
        self.eof_received()

class MySSHServer(asyncssh.SSHServer):
    def session_requested(self) -> asyncssh.SSHServerSession:
        return MySSHServerSession()

async def start_server() -> None:
    await asyncssh.create_server(MySSHServer, '', 8022,
                                 server_host_keys=['ssh_host_key'],
                                 authorized_client_keys='ssh_user_ca')

loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting server: ' + str(exc))

loop.run_forever()
