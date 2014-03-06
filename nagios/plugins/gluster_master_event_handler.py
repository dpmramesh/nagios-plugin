#!/usr/bin/python
#
# gluster_master_event_handler.py -- Event handler which notifies
# nagios events to Ovirt engine using external events Rest API in Ovirt
#
# Copyright (C) 2014 Red Hat Inc
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#


import argparse
import datetime
import gluster_host_service_handler
import json
import notify_ovirt_engine_handler
import os
from subprocess import Popen, PIPE
import sys

event_handlers = []

def add_event_handler(name, module_name, types):
    event_handler_module = load_event_handler_modules(module_name)
    event_handlers.append({'name':name, 'types':types, 'module':event_handler_module})
    

def load_event_handler_modules(module_name):
    module_names = []
    module_names.append(module_name)
    module = map(__import__, module_names)
    return module[0]
    
    
def init_all_event_handlers():
    add_event_handler('notify_ovirt_engine_handler', 'notify_ovirt_engine_handler', ['Brick','CPU'])
    add_event_handler('gluster_host_service_handler', 'gluster_host_service_handler', ['Brick','Disk','CPU','Memory','Physical'])


def get_event_handlers():
    return event_handlers


def process_gluster_event_handlers(args):
    init_all_event_handlers()
    event_handlers = get_event_handlers()
        
    for event_handler in event_handlers:
        if args.glusterEntity in event_handler['types']:
            try:
                event_handler['module'].handle_nagios_event(args)
            except Exception as exp:
                print exp


# Main Method
if __name__ == "__main__":
	
    parser = argparse.ArgumentParser(description="Master event handler for gluster events. Internally it will call the event handlers configured for the service")
    parser.add_argument('-c', '--cluster', action='store', dest='cluster',
					type=str, required =True, help='Cluster name')
    parser.add_argument('-H','--host', action='store', dest='host',
					type=str, required =True, help='Host name')
    parser.add_argument('-g','--glusterEntity', action='store', dest='glusterEntity',
					type=str, required =True, help='Gluster entity')
    parser.add_argument('-s', '--service', action='store', dest='service',
                        type=str, required =True, help='Service name')
    parser.add_argument('-S','--status', action='store', dest='status',
					type=str, required =True, help='Service''s new status')
    parser.add_argument('-t','--stateType', action='store', dest='stateType',
                    type=str, required =True, help='Service state type')
    parser.add_argument('-a','--attempts', action='store', dest='attempts',
                    type=str, required =True, help='No. of attempts to check the service status')
    parser.add_argument('-e','--eventId', action='store', dest='event_id',
					type=str, required =True, help='Global Nagios event ID')
    parser.add_argument('-o','--ovirtServer', action='store', dest='ovirt_engine_url',
                    type=str, required =True, help='Ovirt Engine Rest API URL')
    parser.add_argument('-u','--username', action='store', dest='username',
                    type=str, required =True, help='Ovirt user name')
    parser.add_argument('-p','--password', action='store', dest='password',
                    type=str, required =False, help='Ovirt password')
    parser.add_argument('-C','--cert_file', action='store', dest='cert_file',
                        type=str, required =False, help='CA certificate of the Ovirt Engine')
    args = parser.parse_args()
    process_gluster_event_handlers(args)
