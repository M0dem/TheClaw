#!/usr/bin/env python

# Just a helper module that contains a few miscellaneous functions.


import re
import unicodedata


# convert bytes to kilobytes
def byte_kb(self, b, place = 2):
    kb = float(b) / 1024
    return rount(float(kb), place)

# convert bytes to megabytes
def byte_mb(self, b, place = 2):
    mb = float(float(b) / 1024) / 1024
    return round(float(mb), place)

# make a string "filename ready"
def slugify(self, value):
    # will choke if not unicode
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value
