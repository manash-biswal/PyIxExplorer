#!/usr/bin/env python

import logging
import sys

from ixexplorer.pyixia import Port
from ixexplorer.ixe_app import IxeApp

host = '192.168.42.174'
# For Linux servers use 8022
tcp_port = 8022
# Required only for Linux servers
rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/8.20-EA/TclScripts/lib/ixTcl1.0/id_rsa'

def link_state_str(link_state):
    prefix = 'LINK_STATE_'
    for attr in dir(Port):
        if attr.startswith(prefix):
            val = getattr(Port, attr)
            if val == link_state:
                return attr[len(prefix):]
    return link_state

def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(logging.FileHandler('c:/temp/ixeooapi.log'))
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    i = IxeApp(logging.getLogger(), host, tcp_port, rsa_id)
    i.connect()
    i.discover()

    print i.chassis.type_name
    print ''

    print '%-4s | %-32s | %-10s | %s' % ('Card', 'Type', 'HW Version', 'Serial Number')
    print '-----+----------------------------------+------------+--------------'
    for card in i.chassis.cards:
        if card is not None:
            print '%-4s | %-32s | %-10s | %-s' % (card, card.type_name, card.hw_version, card.serial_number)
    print ''

    print '%-8s | %-8s | %-10s | %-s' % ('Port', 'Owner', 'Link State', 'Speeds')
    print '---------+----------+------------+-------------------------------'
    for card in i.chassis.cards:
        if card is None:
            continue
        for port in card.ports:
            print '%-8s | %-8s | %-10s | %-s' % (port, port.owner.strip(), link_state_str(port.link_state),
                                                 port.supported_speeds())

    i.disconnect()

if __name__ == '__main__':
    main()
