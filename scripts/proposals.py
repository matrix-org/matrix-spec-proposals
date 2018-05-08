# proposals.py: generate an RST file (proposals.rst) from queries to github.com/matrix.org/matrix-doc/issues.
# v0.0.1
# todo:
#   use status labels to create separate sections.
#   include all fields discussed at https://docs.google.com/document/d/1wLln7da12l0H5YgAh5xM2TVE7VsTjXzhEwVh3sRBMCk/edit#
#   format, probably as tables

import requests
import re
from datetime import datetime
from m2r import convert as m2r

pagecount = 1

def getpage(url, page):
    resp = requests.get(url + str(page))

    for link in resp.links.values():
        if link['rel'] == 'last':
            pagecount = re.search('page=(.+?)', link['url']).group(1)

    return resp.json()

def getbylabel(label):
    pagecount = 1
    json = list()
    urlbase = 'https://api.github.com/repos/matrix-org/matrix-doc/issues?state=open&labels=' + label + '&page='
    print(urlbase)
    json.extend(getpage(urlbase, 1))
    for page in range(2, int(pagecount) + 1):
        getpage(urlbase, page)

    return json

# new status labels:
# proposal-ready-for-review,rejected,stalled,merged,spec-pr-in-review,proposal-wip,proposal-in-review,spec-pr-ready-for-review,proposal-passed-review
labels = ['p1', 'p2']
issues = {}

for label in labels:
    issues[label] = getbylabel(label)
    print(issues)

text_file = open("../specification/proposals.rst", "w")

text_file.write("Tables\n------------------\n\n")


for label in labels:
    text_file.write(label + "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    text_file.write(".. list-table::\n   :header-rows: 1\n   :widths: auto\n\n")
    text_file.write("   * - ID\n")
    text_file.write("     - github username\n")
    text_file.write("     - proposal title\n")
    text_file.write("     - created_at\n")
    text_file.write("     - updated_at\n")
    text_file.write("     - maindoc\n")

    for item in issues[label]:
        maindoc = re.search('Documentation: (.+?)\n', str(item['body']))
        if maindoc is not None:
            maindoc = maindoc.group(1)
        text_file.write("   * - `" + str(item['number']) + " <" + item['html_url'] + ">`_\n")
        text_file.write("     - " + item['user']['login'] + "\n")
        text_file.write("     - " + item['title'] + "\n")
        text_file.write("     - " + item['created_at'] + "\n")
        text_file.write("     - " + item['updated_at'] + "\n")
        text_file.write("     - " + str(maindoc) + "\n")
    text_file.write("\n\n\n")

text_file.write("\n")


# text_file.write("The Proposals List\n------------------\n")
# # text_file.write(json[0]['user']['login'])
# for item in json:
#     # write a header
#     prop_header = item['title'] + " (" + str(item['number']) + ")"
#     text_file.write(prop_header + "\n")
#     text_file.write("~" * len(prop_header))
#     text_file.write("\n\n")

#     # write some metadata
#     text_file.write(item['created_at'] + "\n")
#     text_file.write(item['updated_at'] + "\n")
#     # created = datetime.strptime(item['created_at'], "%Y-%m-%dT%XZ")


#     # write body text
#     body = m2r(str(item['body']))
#     text_file.write(body + "\n\n\n")

text_file.close()
