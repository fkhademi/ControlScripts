#!/usr/bin/python
import os
import sys
import json
import infoblox
from avi.sdk.avi_api import ApiSession
from requests.packages import urllib3
urllib3.disable_warnings()

def ParseAviParams(api, tenant, argv):
    if len(argv) != 2:
        return
    #Load the arguments
    alert_dict = json.loads(argv[1])
    #Get the deleted object
    alert_obj = alert_dict["events"][0]["event_details"]["config_delete_details"]["resource_data"]
    old_obj = json.loads(alert_obj)
    # Only continue if VS is an SNI child VS
    if old_obj['type'] == 'VS_TYPE_VH_CHILD':
        return old_obj
    else:
        exit()

def GetVSParentObject(api, parent_ref):
    # Get the parent object
    parent_obj = api.get(parent_ref.split('/api/')[1])
    parent_vs = parent_obj.json()
    vip = parent_vs['ip_address']['addr']
    return vip

def DelHosts(vs_hostnames, vip, ibx):
    # Make sure Host record does not already exist
    for hostname in vs_hostnames:
        # Validate hostname exists
        try:
            ibxhost=ibx.get_host(hostname)
        except Exception as e:
            print "[SKIPPING] %s" %e
        else:
            host_ip=ibxhost['ipv4addrs'][0]['ipv4addr']
            if host_ip != vip:
                print "[ERROR] IP mismatch %s != %s for hostname %s" % (host_ip, vip, hostname)
            elif host_ip == vip:
                try:
                    ibxhost=ibx.delete_host_record(hostname)
                except Exception as e:
                    print "[ERROR] %s" %e
                else:
                    print "[DELETED] Host %s was deleted.." %hostname


# Get session on the basis of authentication token
token=os.environ.get('API_TOKEN')
user=os.environ.get('USER')
tenant=os.environ.get('TENANT')
print "[INFO] token: %s" % token
print "[INFO] user: %s" % user
print "[INFO] tenant: %s" % tenant

ibx_server='10.56.70.250'
ibx_username='frey'
ibx_password='avi123$%'
ibx_version='2.0'
ibx_dns_view='default'
ibx_net_view='default'


with ApiSession("localhost", user, token=token, tenant=tenant) as session:
    vs_obj = ParseAviParams(session, tenant, sys.argv)
    vs_hostnames = vs_obj['vh_domain_name']
    vs_parent_ref = vs_obj['vh_parent_vs_ref']
    vs_parent_vip = GetVSParentObject(session, vs_parent_ref)
    #Open connection to Infoblox
    ibx=infoblox.Infoblox(ibx_server, ibx_username, ibx_password, ibx_version, ibx_dns_view, ibx_net_view, iba_verify_ssl=False)
    DelHosts(vs_hostnames, vs_parent_vip, ibx)
