# proposals.py: generate an RST file (proposals.rst) from queries to github.com/matrix.org/matrix-doc/issues.
# v0.0.1
# todo:
#   use status labels to create separate sections.
#   include all fields discussed at https://docs.google.com/document/d/1wLln7da12l0H5YgAh5xM2TVE7VsTjXzhEwVh3sRBMCk/edit#
#   format, probably as tables

import requests
import re
from m2r import convert as m2r

def getpage(url, page):
    resp = requests.get(url + str(page))
    json.extend(resp.json())

    for link in resp.links.values():
        if link['rel'] == 'last':
            return re.search('page=(.+?)', link['url']).group(1)

json = list()
print("json:" + str(len(json)))
pagecount = getpage('https://api.github.com/repos/matrix-org/matrix-doc/issues?labels=spec-omission&state=open&page=', 1)
print("json:" + str(len(json)))
print("pagecount:" + str(pagecount))
for page in range(2, int(pagecount) + 1):
    getpage('https://api.github.com/repos/matrix-org/matrix-doc/issues?labels=spec-omission&state=open&page=', page)
    print("json:" + str(len(json)))
    print("currentpage:" + str(page))
    print("pagecount:" + str(pagecount))
    print("json:" + str(len(json)))


text_file = open("../specification/proposals.rst", "w")

text_file.write(".. contents:: Table of Contents\n")
text_file.write(".. sectnum::")
text_file.write("\n")
text_file.write("\n")
text_file.write("The Proposals List\n------------------\n")
# text_file.write(json[0]['user']['login'])

for item in json:
    prop_header = item['title'] + " (" + str(item['number']) + ")"
    text_file.write(prop_header + "\n")
    text_file.write("~" * len(prop_header))
    text_file.write("\n\n")
    body = m2r(str(item['body']))
    text_file.write(body + "\n\n\n")

text_file.close()
