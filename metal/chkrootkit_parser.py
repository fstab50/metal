"""
chkrootkit parser
"""

with open('chkrootkit.report') as f1:
    lines = f1.readlines()
    for i in range(0, len(lines)):
        if lines[i].startswith('Searching for suspicious files and dirs'):
            suspicious_file = lines[i + 1]
    suspicious_list = suspicious_file.split(' ')
