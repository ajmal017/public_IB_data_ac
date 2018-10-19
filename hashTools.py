"""This file contains tools for getting a hash of whatever file you're working in. Useful for tracking which version
of which predictor, position taker, etc., """

import hashlib
import subprocess

def getmd5(filename):
    hasher = hashlib.md5()
    with open(filename, 'r') as f:
        for line in f.readlines():
            hasher.update(line.encode(encoding='utf-8'))
    return hasher.hexdigest()

def get_git_revision_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

__CURRENT_GIT_HASH__ = get_git_revision_hash()  # Useful to have this in a variable so functions
                                                # don't have to run the function over and over.
