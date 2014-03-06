#!/usr/bin/python
#
# notify_ovirt_engine_handler.py -- Event handler which notifies
# nagios events to ovrit engine using events Rest API in Ovirt
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


import sys
import datetime
from subprocess import Popen, PIPE
import json
import getopt
import os

# Shows the usage of the script
def showUsage():
    usage = "Usage: %s -c <Cluster Name> -h <Host Name> -s <Service Name> -t <Service Status> -e <Nagios Event ID> -o <Ovirt Server URL> -u <User Name> -p <Password>\n" % os.path.basename(sys.argv[0])
    sys.stderr.write(usage)

def postOvirtExternalEvent(serverurl, username, password, bodydata, cookie):
	externalCommand = ["curl", "--insecure", "--request",  "POST", "--header", "Accept: application/json", "--header", "Content-Type: application/xml", "--header",  "Prefer: persistent-auth", "--user",  username + ":" + password, "--cookie",  cookie, "--cookie-jar",  cookie, "--data",  bodydata, serverurl + "/events" ]
	process= Popen(externalCommand, stdout=PIPE, stderr=PIPE)
	output = process.communicate()[0]
	return output

def composeEventDescription(service, host, cluster, status):
	return "%s status of host %s in Cluster %s changed to %s" % (service, host, cluster, status)
def handleNagiosEvent(cluster, host, service, status, globalEventId, ovirtEngine, username, password):
	COOKIES_FILE = "/tmp/cookies.txt"
	severity = 'NORMAL'

	if(status == 'CRITICAL'):
	        severity = 'ALERT'

	description = composeEventDescription(service, host, cluster, status)
	bodyData = "<event><origin>Nagios</origin><severity>%s</severity><description>%s</description> <custom_id>%s</custom_id></event>" % (severity, description, globalEventId)
	return postOvirtExternalEvent(ovirtEngine, username, password, bodyData, COOKIES_FILE)

# Main Method
if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hc:n:s:t:e:o:u:p:", ["help", "cluster=", "host=", "service=", "status=", "eventId=", "ovirtServer=", "username=", "password="])
	except getopt.GetoptError as exp:
		print(str(exp))
		showUsage()
		sys.exit(-1)
	cluster = ''
	host = ''
	service =''
	status = ''
	nagiosEventId = ''
	ovirtEngineUrl = ''
	ovirtUser =''
	ovirtPassword = ''
	if( len(opts) == 0 ):
		showUsage()
	else:
		for opt,arg in opts:
			if( opt in('-h', '--help') ):
				showUsage()
				sys.exit()
			elif( opt in('-c', '--cluster') ):
				cluster = arg
			elif( opt in('-n', '--host') ):
				host = arg
		        elif( opt in('-s', '--service') ):
				service = arg
			elif( opt in('-t', '--status') ):
				status = arg
			elif( opt in('-e', '--eventId') ):
				nagiosEventId = arg
			elif( opt in('-o', '--ovirtServer') ):
				ovirtEngineUrl = arg
			elif( opt in('-u', '--username') ):
				ovirtUser = arg
			elif( opt in('-p', '--password') ):
				ovirtPassword = arg
			else:
				showUsage()
				sys.exit()

	# Notifies Ovirt Engine about service/host state change
		response = handleNagiosEvent(cluster, host, service, status, nagiosEventId, ovirtEngineUrl, ovirtUser, ovirtPassword)
		responsedata = json.loads(response)
		exitStatus = 0
		if (responsedata.get("id") == None):
			print "Failed to submit event %s to ovirt engine at %s" % (nagiosEventId, ovirtEngineUrl)
			exitStatus = -1
		else:
			print "Nagios event %s posted to ovirt engine  %s " % (nagiosEventId, responsedata['href'])
		sys.exit(exitStatus)
