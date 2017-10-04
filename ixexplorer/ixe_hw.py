# Copyright (c) 2015  Kontron Europe GmbH
#
# This module is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this module; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from os import path
import re

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, IxTclHalError
from ixexplorer.ixe_object import IxeObject
from argh.compat import OrderedDict


class PortGroup(IxeObject):
    START_TRANSMIT = 7
    STOP_TRANSMIT = 8
    START_CAPTURE = 9
    STOP_CAPTURE = 10
    RESET_STATISTICS = 13
    PAUSE_TRANSMIT = 15
    STEP_TRANSMIT = 16
    TRANSMIT_PING = 17
    TAKE_OWNERSHIP = 40
    TAKE_OWNERSHIP_FORCED = 41
    CLEAR_OWNERSHIP = 42
    CLEAR_OWNERSHIP_FORCED = 43

    __tcl_command__ = 'portGroup'
    __tcl_members__ = [
            TclMember('lastTimeStamp', type=int, flags=FLAG_RDONLY),
    ]

    __tcl_commands__ = ['create', 'destroy']

    next_free_id = 1

    def __init__(self, pg_id=None):
        if not pg_id:
            pg_id = PortGroup.next_free_id
            PortGroup.next_free_id += 1
        super(self.__class__, self).__init__(objRef=pg_id, parent=None)

    def add_port(self, port):
        self._ix_command('add', port.obj_ref())

    def del_port(self, port):
        self._ix_command('del', port.obj_ref())

    def _set_command(self, cmd):
        self.api.call_rc('portGroup setCommand {} {}'.format(self.obj_ref(), cmd))

    def start_transmit(self):
        self._set_command(self.START_TRANSMIT)

    def stop_transmit(self):
        self._set_command(self.STOP_TRANSMIT)

    def start_capture(self):
        self._set_command(self.START_CAPTURE)

    def stop_capture(self):
        self._set_command(self.STOP_CAPTURE)

    def reset_statistics(self):
        self._set_command(self.RESET_STATISTICS)

    def pause_transmit(self):
        self._set_command(self.PAUSE_TRANSMIT)

    def step_transmit(self):
        self._set_command(self.STEP_TRANSMIT)

    def transmit_ping(self):
        self._set_command(self.TRANSMIT_PING)

    def take_ownership(self, force=False):
        if not force:
            self._set_command(self.TAKE_OWNERSHIP)
        else:
            self._set_command(self.TAKE_OWNERSHIP_FORCED)

    def clear_ownership(self, force=False):
        if not force:
            self._set_command(self.CLEAR_OWNERSHIP)
        else:
            self._set_command(self.CLEAR_OWNERSHIP_FORCED)


class Statistics(IxeObject):
    """Per port statistics."""

    __tcl_command__ = 'stat'
    __tcl_members__ = [
            TclMember('bytesReceived', type=int, flags=FLAG_RDONLY),
            TclMember('bytesSent', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent):
        super(self.__class__, self).__init__(objRef=parent.obj_ref(), parent=parent)

    def _ix_get(self, member):
        self.api.call('stat get {} {}'.format(member.name, self.obj_ref()))

    def _ix_set(self, member):
        self.api.call('stat set {} {}'.format(member.name, self.obj_ref()))


class Port(IxeObject):
    __tcl_command__ = 'port'
    __tcl_members__ = [
            TclMember('name'),
            TclMember('owner', flags=FLAG_RDONLY),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('loopback'),
            TclMember('flowControl'),
            TclMember('linkState', type=int, flags=FLAG_RDONLY),
            TclMember('portMode', type=int),
            TclMember('transmitMode'),
    ]

    __tcl_commands__ = ['export', 'getFeature', 'reset', 'setFactoryDefaults', 'write']

    LINK_STATE_DOWN = 0
    LINK_STATE_UP = 1
    LINK_STATE_LOOPBACK = 2
    LINK_STATE_MII_WRITE = 3
    LINK_STATE_RESTART_AUTO = 4
    LINK_STATE_AUTO_NEGOTIATING = 5
    LINK_STATE_MII_FAIL = 6
    LINK_STATE_NO_TRANSCEIVER = 7
    LINK_STATE_INVALID_ADDRESS = 8
    LINK_STATE_READ_LINK_PARTNER = 9
    LINK_STATE_NO_LINK_PARTNER = 10
    LINK_STATE_RESTART_AUTO_END = 11
    LINK_STATE_FPGA_DOWNLOAD_FAILED = 12
    LINK_STATE_LOSS_OF_FRAME = 24
    LINK_STATE_LOSS_OF_SIGNAL = 25

    def __init__(self, parent, port_id):
        super(self.__class__, self).__init__(objRef=parent.obj_ref() + ' ' + str(port_id), parent=parent)
        self.stats = Statistics(self)

    def _ix_get(self, member):
        self._api.call_rc('port get %d %d %d', *self._port_id())

    def _ix_set(self, member):
        self._api.call_rc('port set %d %d %d', *self._port_id())

    def supported_speeds(self):
        return re.findall(r'\d+', self.get_feature('ethernetLineRate'))

    def reserve(self, force=False):
        if not force:
            self.api.call_rc('ixPortTakeOwnership {}'.format(self.obj_ref()))
        else:
            self.api.call_rc('ixPortTakeOwnership {} force'.format(self.obj_ref()))

    def release(self):
        self.api.call_rc('ixPortClearOwnership {}'.format(self.obj_ref()))

    def load_config(self, config_file_name):
        """ Load configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file_name: full path to the configuration file.
        :todo: add support for str files.
        """

        ext = path.splitext(config_file_name)[-1].lower()
        if ext == '.prt':
            self.api.call_rc('port import {} {}'.format(config_file_name, self.obj_ref()))
        elif ext == '.str':
            self.reset()
            self.api.call_rc('stream import {} {}'.format(config_file_name, self.obj_ref()))
        else:
            raise ValueError('Configuration file type {} not supported.'.format(ext))
        self.write()


class Card(IxeObject):
    __tcl_command__ = 'card'
    __tcl_members__ = [
            TclMember('cardOperationMode', type=int, flags=FLAG_RDONLY),
            TclMember('clockRxRisingEdge', type=int),
            TclMember('clockSelect', type=int),
            TclMember('clockTxRisingEdge', type=int),
            TclMember('fpgaVersion', type=int, flags=FLAG_RDONLY),
            TclMember('hwVersion', type=int, flags=FLAG_RDONLY),
            TclMember('portCount', type=int, flags=FLAG_RDONLY),
            TclMember('serialNumber', flags=FLAG_RDONLY),
            TclMember('txFrequencyDeviation', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName'),
    ]

    TYPE_NONE = 0

    def __init__(self, parent, chassis_id, card_id):
        super(self.__class__, self).__init__(objRef=str(chassis_id) + ' ' + str(card_id), parent=parent)
        self.ports = []

    def _ix_get(self, member):
        self.api.call_rc('card get {}'.format(self.obj_ref()))

    def _ix_set(self, member):
        self.api.call_rc('card set {}'.format(self.obj_ref()))

    def discover(self):
        for pid in range(self.port_count):
            pid += 1
            port = Port(self, pid)
            self.logger.info('Adding port %s', port)
            self.ports.append(port)

    def add_vm_port(self, port_id, nic_id, mac, promiscuous=0, mtu=1500, speed=1000):
        card_id = self._card_id()
        self._api.call_rc('card addVMPort {} {} {} {} {} {} {} {}'.
                          format(card_id[0], card_id[1], port_id, nic_id, promiscuous, mac, mtu, speed))
        return Port(self._api, self, port_id)

    def remove_vm_port(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))


class Chassis(IxeObject):
    __tcl_command__ = 'chassis'
    __tcl_members__ = [
            TclMember('baseIpAddress'),
            TclMember('cableLength', type=int),
            TclMember('hostName', flags=FLAG_RDONLY),
            TclMember('id', type=int),
            TclMember('ipAddress', flags=FLAG_RDONLY),
            TclMember('ixServerVersion', flags=FLAG_RDONLY),
            TclMember('master', flags=FLAG_RDONLY),
            TclMember('maxCardCount', type=int, flags=FLAG_RDONLY),
            TclMember('name'),
            TclMember('operatingSystem', type=int, flags=FLAG_RDONLY),
            TclMember('sequence', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName', flags=FLAG_RDONLY),
    ]

    __tcl_commands__ = ['add']

    TYPE_1600 = 2
    TYPE_200 = 3
    TYPE_400 = 4
    TYPE_100 = 5
    TYPE_400C = 6
    TYPE_1600T = 7
    TYPE_DEMO = 9
    TYPE_OPTIXIA = 10
    TYPE_OPIXJR = 11
    TYPE_400T = 14
    TYPE_250 = 17
    TYPE_400TF = 18
    TYPE_OPTIXIAX16 = 19
    TYPE_OPTIXIAXL10 = 20
    TYPE_OPTIXIAXM12 = 22
    TYPE_OPTIXIAXV = 24

    TYPES = {2: 'ixia1600', 'ixia1600': 2,
             3: 'ixia200', 'ixia200': 3,
             4: 'ixia400', 'ixia400': 4,
             5: 'ixia100', 'ixia100': 5,
             6: 'ixia400C', 'ixia400C': 6,
             7: 'ixia1600T', 'ixia1600T': 7,
             9: 'ixiaDemo', 'ixiaDemo': 9,
             10: 'ixiaOptixia', 'ixiaOptixia': 10,
             11: 'ixiaOpixJr', 'ixiaOpixJr': 11,
             14: 'ixia400T', 'ixia400T': 14,
             17: 'ixia250', 'ixia250': 17,
             18: 'ixia400Tf', 'ixia400Tf': 18,
             19: 'ixiaOptixiaX16', 'ixiaOptixiaX16': 19,
             20: 'ixiaOptixiaXL10', 'ixiaOptixiaXL10': 20,
             22: 'ixiaOptixiaXM12', 'ixiaOptixiaXM12': 22,
             24: 'ixiaOptixiaXV', 'ixiaOptixiaXV': 24}

    OS_UNKNOWN = 0
    OS_WIN95 = 1
    OS_WINNT = 2
    OS_WIN2000 = 3
    OS_WINXP = 4

    def __init__(self, host, chassis_id=1):
        super(self.__class__, self).__init__(objRef=host, parent=None, name=host)
        self.chassis_id = chassis_id
        self.cards = []

    def _ix_get(self, member):
        self.api.call_rc('chassis get %s', self.obj_ref())

    def _ix_set(self, member):
        self.api.call_rc('chassis set %s', self.obj_ref())

    def connect(self):
        self.add()
        self.id = self.chassis_id

    def disconnect(self):
        self._ix_command('del')

    def discover(self):
        self.logger.info('Discover chassis {}'.format(self.obj_name()))
        for cid in range(self.max_card_count):
            # unfortunately there is no config option which cards are used. So
            # we have to iterate over all possible card ids and check if we are
            # able to get a handle.
            cid += 1
            try:
                card = Card(self, self.chassis_id, cid)
                self.logger.info('Adding card %s (%s)', card, card.type_name)
                card.discover()
                self.cards.append(card)
            except IxTclHalError:
                # keep in sync with card ids
                self.cards.append(None)

    def add_vm_card(self, card_ip, card_id, keep_alive=300):
        self._api.call_rc('chassis addVirtualCard {} {} {} {}'.format(self.host, card_ip, card_id, keep_alive))
        return Card(self._api, self, card_id)

    def remove_vm_card(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))

    def get_ports(self):
        """
        :return: dictionary {name: object} of all ports.
        """

        ports = OrderedDict()
        for c in filter(None, self.cards):
            ports.update({str(p): p for p in c.ports})
        return ports