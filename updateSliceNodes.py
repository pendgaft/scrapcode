#!/usr/bin/python3
"""
author: pendgaft
adapted (i.e. basically copied and updated) from work by Brian Sanderson

Downloads boot nodes into slice and generates node lists.

Resultant files (suppressed via -q):
  all-nodes.txt - all nodes ever found by this script
  slice-nodes.txt - all nodes currently part of the slice
  lie-nodes.txt - all nodes returned as in the boot_state by PLC
"""

import sys
import xmlrpc.client
import getpass

write_new_nodes = '-n' in sys.argv
remove_nbnodes = '-r' in sys.argv
suppress_writes = '-q' in sys.argv

api_server = xmlrpc.client.ServerProxy('https://www.planet-lab.org/PLCAPI/')

# in Python, this creates a dictionary, or associative array.
auth= {}
auth['Username']= "schuch@cs.umn.edu"
# always 'password', for password based authentication
auth['AuthMethod']= "password"
auth['AuthString']= getpass.getpass()
# valid roles include, 'user', 'tech', 'pi', 'admin'
auth['Role']= "user"
slice_name = 'umn_hopper'

# use the AdmAuthCheck function to make sure we
# are authorized and can make api calls
print("Authorizing Planet-lab ... ", end="", flush=True)
authorized = api_server.AuthCheck(auth)
if authorized:
	print("[SUCCESS]")
else:
	print("[FAILURE] Permission denied.")
	sys.exit()

return_fields = ['hostname','boot_state']

# get the all the nodes, regardless of current boot state
print("Retrieving node lists ...", end="", flush=True)
all_nodes = api_server.GetNodes(auth, {}, ['node_id', 'hostname', 'boot_state'])
print("found " + str(len(all_nodes)) + " nodes")

have_node_ids = api_server.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in api_server.GetNodes(auth, have_node_ids, ['hostname'])]

toadd_nodes = []
todel_nodes = []
live_nodes = []

# nodes is an array of associative arrays/dictionary objects, each one
# corresponding to a node returned. the keys in each array element are
# the keys specified in return_fields

for node_record in all_nodes:
	if node_record['boot_state'] == 'boot':
		live_nodes.append(node_record['hostname'])
		if node_record['hostname'] not in have_nodes:
			toadd_nodes.append(node_record['hostname'])
	elif (node_record['hostname'] in have_nodes) and node_record['boot_state'] != 'boot':
		todel_nodes.append(node_record['hostname'])

print("Found %d live node(s)" % (len(live_nodes)))
print("Found %d new boot node(s)" % (len(toadd_nodes)))
print("Found %d node(s) no longer in boot state" % (len(todel_nodes)))

if len(toadd_nodes) > 0:
	# add node to slice
        print("Adding new nodes to slice ...", end="", flush=True)
        result = api_server.AddSliceToNodes(auth, slice_name, toadd_nodes)
        if result == 1:
                print("SUCCESS")
        else:
                print("FAILED!")
        sys.stdout.flush()
#        if (not suppress_writes) and write_new_nodes:
#	        fp = open('new-nodes.txt','w')
#	        for node in toadd_nodes:
#		        fp.write("%s\n" % (node))
#               fp.close()

if remove_nbnodes and len(todel_nodes) > 0:
	#remove nodes from slice
	print("Removing non-boot nodes from slice ...", end="", flush=True)
	result = api_server.SliceNodesDel(auth, slice_name, todel_nodes)
	if result == 1:
		print("SUCCESS")
	else:
		print("FALIED!")
	sys.stdout.flush()

if not suppress_writes:
	print("Writing out all node list ...", end="", flush=True)
	
	# find out current nodes
	merged_nodes = set([])
	afp = open('all-nodes.txt', 'r')
	for node in afp:
		merged_nodes.add(node.strip())
	afp.close()

	# add in all found nodes
	for node in all_nodes:
		merged_nodes.add(node['hostname'].strip())
	
	# write out all node list
	afp = open('all-nodes.txt','w')
	for node in merged_nodes:
		afp.write("%s\n" % (node))
	afp.close()
	print("done.")

	# write out current node list
	print("Writing out current node list ...", end="", flush=True)

	have_node_ids = api_server.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
	have_nodes = [node['hostname'] for node in api_server.GetNodes(auth, have_node_ids, ['hostname'])]
	
	cfp = open('slice-nodes.txt','w')
	for node in have_nodes:
		cfp.write("%s\n" % (node))
	cfp.close()
	print("done.")

	print("Writing out live node list ...", end="", flush=True)
	lfp = open("live-nodes.txt", "w")
	for tHost in live_nodes:
		lfp.write("%s\n" % (tHost))
	lfp.close()
	print("done.")
