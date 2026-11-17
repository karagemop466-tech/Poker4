#!/usr/bin/env python3
"""Union-resolve COORDINATION.md conflict markers: keep both sides, drop markers."""
lines = open('COORDINATION.md').read().split('\n')
out, i, n = [], 0, 0
while i < len(lines):
    if lines[i].startswith('<<<<<<<'):
        n += 1
        head, theirs = [], []
        i += 1
        while not lines[i].startswith('======='):
            head.append(lines[i]); i += 1
        i += 1
        while not lines[i].startswith('>>>>>>>'):
            theirs.append(lines[i]); i += 1
        i += 1
        out.extend(head); out.extend(theirs)
    else:
        out.append(lines[i]); i += 1
open('COORDINATION.md', 'w').write('\n'.join(out))
left = sum(1 for l in out if l.startswith(('<<<<<<<', '>>>>>>>')) or l == '=======')
print(f'resolved {n} conflict block(s); markers left: {left}')
