#!/usr/bin/env python3

import re
import subprocess

MEM_SIZE = re.compile("([0-9]+)\\s+.B")

def main(hostFile):
    memResults = {}
    ulimResults = {}
    hostFileFP = open(hostFile, "r")
    hosts = []
    for line in hostFileFP:
        line = line.strip()
        if len(line) > 0:
            hosts.append(line)
    hostFileFP.close()
    print("starting querries")
    counter = 0
    nextPoint = len(hosts) / 10
    for host in hosts:
        sizeKB = queryMem(host)
        if sizeKB > 0:
            memResults[host] = sizeKB / (1024.0 * 1024.0)
        counter = counter + 1
        if counter == nextPoint:
            print(str(float(counter) / float(len(hosts))) + "% done")
            nextPoint = nextPoint + len(hosts) / 10
    print("done with querries, starting sorting")
    top200Mem = topN(memResults, 200)
    outFP = open("high-mem.txt", "w")
    printList(top200Mem, memResults, outFP)
    outFP.close()

def printList(incList, incMap, outFP=None):
    for tItem in incList:
        if outFP == None:
            print(tItem + "," + str(incMap[tItem]))
        else:
            outFP.write(tItem + "," + str(incMap[tItem]) + "\n")
            
def topN(incMap, n):
    if len(incMap) < n:
        n = len(incMap)
    topList = []
    while len(topList) < n:
        currentTop = None
        currentVal = 0.0
        for tKey in incMap:
            if (tKey not in topList) and incMap[tKey] > currentVal:
                currentVal = incMap[tKey]
                currentTop = tKey
        topList.append(currentTop)
    return topList

def execCmd(host, cmd):
    result = []
    try:
        sshProc = subprocess.run(["cat", "/proc/meminfo"], stdout = subprocess.PIPE, universal_newlines=True)
#        sshProc = subprocess.run(["ssh", "-l", "umn_hopper", "-o", "StrictHostKeyChecking=no", host, cmd], stdout = subprocess.PIPE, timeout=2, universal_newlines=True)
        for line in sshProc.stdout:    
            result.append(line)
    except subprocess.TimeoutExpired:
        print("timeout")
        return None
    except subprocess.SubprocessError:
        print("err")
        return None
    return "".join(result).split("\n")

def queryUlimit(host):
    ulimitResult = execCmd(host, "ulimit -n")
    for line in ulimitResult:
        line = line.strip()
        if line.isnumeric():
            return int(line)
    return -1

def queryMem(host):
    memResult = execCmd(host, "cat /proc/meminfo")
    for line in memResult:
        if "MemFree" in line:
            matcher = MEM_SIZE.search(line)
            if matcher:
                return float(matcher.group(1))
    return -1


if __name__ == "__main__":
    out = execCmd("foo", "bar")
    print(str(len(out)))

