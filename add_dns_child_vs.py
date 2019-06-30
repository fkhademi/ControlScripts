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
    #Get the VS name
    vs_name = alert_dict["obj_name"]
    return vs_name

def GetVSObject(api, vs_name, tenant):
    # Get the Avi VS object, only continue if is an SNI child VS
    vs_obj = api.get_object_by_name('virtualservice', vs_name, tenant=tenant)
    vs_type = vs_obj['type']
    if vs_type == 'VS_TYPE_VH_CHILD':
        return vs_obj
    else:
        exit()

def GetVSParentObject(api, parent_ref):
    # Get the parent object
    parent_obj = api.get(parent_ref.split('/api/')[1])
    parent_vs = parent_obj.json()
    vip = parent_vs['ip_address']['addr']
    return vip

def AddHosts(vs_hostnames, vip, ibx):
    # Make sure Host record does not already exist
    for hostname in vs_hostnames:
        # Validate hostname exists
        try:
            ibxhost=ibx.get_host(hostname)
        except Exception as e:
            print "[INFO] %s" %e
            try:
                new_ib_host = ibx.create_host_record(vip, hostname)
                #print new_ib_host
            except Exception as e:
                print "[ERROR] %s" %e
            else:
                print "[ADDED] Created Host: %s, IP Address: %s ..." % (hostname, vip)
        else:
            print "[SKIPPED] Host %s already exists.." %hostname


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
    vs_name = ParseAviParams(session, tenant, sys.argv)
    vs = GetVSObject(session, vs_name, tenant)
    vs_hostnames = vs['vh_domain_name']
    vs_parent_ref = vs['vh_parent_vs_ref']
    vs_parent_vip = GetVSParentObject(session, vs_parent_ref)
    #Open connection to Infoblox
    ibx=infoblox.Infoblox(ibx_server, ibx_username, ibx_password, ibx_version, ibx_dns_view, ibx_net_view, iba_verify_ssl=False)
    AddHosts(vs_hostnames, vs_parent_vip, ibx)
