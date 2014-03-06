#!/usr/bin/python
#
# notify_ovirt_engine_handler.py -- Event handler which notifies
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
import json
import os
from subprocess import Popen, PIPE
import sys

COOKIES_FILE = "/tmp/cookies.txt"
SEVERITY_NORMAL = "NORMAL"
SEVERITY_ALERT = "ALERT"
STATUS_CRITICAL = 'CRITICAL'


def post_ovirt_external_event(server_url, username, password, body_data,
                              cert_file, cookie):
    external_command = ["curl", "--request", "POST", "--header",
                        "Accept: application/json",
                        "--header", "Content-Type: application/xml",
                        "--header", "Prefer: persistent-auth"]
    if cert_file is not None:
        external_command.extend(["--cacert", cert_file])
    else:
        external_command.append("--insecure")
    external_command.extend([
							"--user", "%s:%s" %(username,password),
					"--cookie", cookie, "--cookie-jar",
					  cookie, "--data",
					  body_data,
					  "%s/events" % (server_url)])
    process= Popen(external_command, stdout=PIPE, stderr=PIPE)
    output = process.communicate()[0]
    return output


def compose_event_message(service, host, cluster, status):
	return "%s status of host %s in Cluster %s changed to %s" % (service,
																host, cluster, status)

def process_nagios_event(cluster, host, service, status, global_event_id,
					ovirt_engine_url, username, password, cert_file):
	severity = SEVERITY_NORMAL

	if status == STATUS_CRITICAL:
		severity = SEVERITY_ALERT

	description = compose_event_message(service, host, cluster, status)
	body_data = "<event><origin>Nagios</origin><severity>%s</severity>\
				<description>%s</description> <custom_id>%s</custom_id></event>" % (severity, description, global_event_id)
	return post_ovirt_external_event(ovirt_engine_url, username, password,
									body_data, cert_file, COOKIES_FILE)

def handle_nagios_event(args):
    # Notifies Ovirt Engine about service/host state change
    exit_status = 0
    try:
        response = process_nagios_event(args.cluster, args.host, args.service,
                                args.status, args.event_id,
                                args.ovirt_engine_url, args.username, args.password, args.cert_file)
        responsedata = json.loads(response)
        if responsedata.get("id") == None:
            print "Failed to submit event %s to ovirt engine at %s" % (args.event_id, args.ovirt_engine_url)
            exit_status = -1
        else:
            print "Nagios event %s posted to ovirt engine  %s " % (args.event_id, responsedata['href'])

    except Exception as exp:
        print (str(exp))
        exit_status = -1

    return exit_status
    
# Main Method
if __name__ == "__main__":
	
    parser = argparse.ArgumentParser(description="Notifies Nagios events to ovirt engine through external events REAT API")
    parser.add_argument('-c', '--cluster', action='store', dest='cluster',
                    type=str, required =True, help='Cluster name')
    parser.add_argument('-H','--host', action='store', dest='host',
                    type=str, required =True, help='Host name')
    parser.add_argument('-g','--glusterEntity', action='store', dest='gluster_entity',
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
    arguments = parser.parse_args()
    return_status = handle_nagios_event(arguments)
    sys.exit(return_status)
