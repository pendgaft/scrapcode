#!/usr/bin/python2
"""
download_logs.py

@author Brian Sanderson
@date 1/2007

Downloads boot nodes into slice and generates node lists.
"""

import sys
import xmlrpclib
import sets
import getpass

remove_nbnodes = '-r' in sys.argv
no_file_writes = '-n' in sys.argv

api_server = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/')

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
print "Authorizing Planet-lab ... ",
sys.stdout.flush()
authorized = api_server.AuthCheck(auth)
if authorized:
	print "[SUCCESS]"
else:
	print "[FAILURE] Permission denied."
	sys.exit()

return_fields = ['hostname','boot_state']

# get the all the nodes, regardless of current boot state
print "Retrieving node lists ...",
sys.stdout.flush()
all_nodes = api_server.GetNodes(auth, {}, ['node_id', 'hostname', 'boot_state'])
print "found " + str(len(all_nodes)) + " nodes"

have_node_ids = api_server.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
have_nodes = [node['hostname'] for node in api_server.GetNodes(auth, have_node_ids, ['hostname'])]

outFP = open("umn_hopper_nodes.txt", "w")
for tNode in have_nodes:
        outFP.write(tNode + "\n")
outFP.close()
print "done."

toadd_nodes = []
todel_nodes = []

# nodes is an array of associative arrays/dictionary objects, each one
# corresponding to a node returned. the keys in each array element are
# the keys specified in return_fields

for node_record in all_nodes:
	if (node_record['hostname'] not in have_nodes) and node_record['boot_state'] == 'boot':
		toadd_nodes.append(node_record['hostname'])
	elif (node_record['hostname'] in have_nodes) and node_record['boot_state'] != 'boot':
		todel_nodes.append(node_record['hostname'])

print "Found %d new boot node(s)" % (len(toadd_nodes))
print "Found %d node(s) no longer in boot state" % (len(todel_nodes))

if len(toadd_nodes) > 0:
	# add node to slice
	print "Adding new nodes to slice ...",
	sys.stdout.flush()
	result = api_server.AddSliceToNodes(auth, slice_name, toadd_nodes)
	if result == 1:
		print "SUCCESS"
	else:
		print "FAILED!"
	sys.stdout.flush()

	fp = open('new-nodes.txt','w')
	for node in toadd_nodes:
		fp.write("%s\n" % (node));
	fp.close()

if remove_nbnodes and len(todel_nodes) > 0:
	#remove nodes from slice
	print "Removing non-boot nodes from slice ...",
	sys.stdout.flush()
	result = api_server.SliceNodesDel(auth, slice_name, todel_nodes)
	if result == 1:
		print "SUCCESS"
	else:
		print "FALIED!"
	sys.stdout.flush()

if not no_file_writes:
	print "Writing out all node list ...",
	sys.stdout.flush()
	
	# find out current nodes
	merged_nodes = sets.Set()
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
	print "done."

	# write out current node list
	print "Writing out current node list ...",
	sys.stdout.flush()

	have_node_ids = api_server.GetSlices(auth, [ slice_name ], ['node_ids'])[0]['node_ids']
	have_nodes = [node['hostname'] for node in api_server.GetNodes(auth, have_node_ids, ['hostname'])]
	
	cfp = open('current-nodes.txt','w')
	for node in have_nodes:
	        cfp.write("%s\n" % (node))
	cfp.close()
	print "done."

