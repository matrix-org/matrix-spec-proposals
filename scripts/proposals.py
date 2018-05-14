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
authors = set()

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
labels = ['proposal-wip', 'proposal-ready-for-review',
    'proposal-in-review', 'proposal-passed-review',
    'spec-pr-ready-for-review', 'spec-pr-in-review', 'merged', 'abandoned', 'rejected', 'blocked' ]
#labels = ['p1', 'p2', 'p3', 'p4', 'p5']
issues = {}

for label in labels:
    issues[label] = getbylabel(label)
    print(issues)

text_file = open("../specification/proposals.rst", "w")

text_file.write("Tables\n------------------\n\n")


for label in labels:
    if (len(issues[label]) == 0):
        continue

    text_file.write(label + "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    text_file.write(".. list-table::\n   :header-rows: 1\n   :widths: auto\n   :stub-columns: 1\n\n")
    text_file.write("   * - MSC\n")
    text_file.write("     - proposal title\n")
    text_file.write("     - created_at\n")
    text_file.write("     - updated_at\n")
    text_file.write("     - maindoc\n")
    text_file.write("     - author\n")
    text_file.write("     - shepherd\n")

    for item in issues[label]:
        # MSC number
        text_file.write("   * - `MSC" + str(item['number']) + " <" + item['html_url'] + ">`_\n")

        # title from Github issue
        text_file.write("     - " + item['title'] + "\n")

        # created date, find local field, otherwise Github
        created = re.search('^Date: (.+?)\n', str(item['body']), flags=re.MULTILINE)
        if created is not None:
            created = created.group(1).strip()
            try:
                created = datetime.strptime(created, "%d/%m/%Y")
                created = created.strftime('%Y-%m-%d')
            except:
                pass

            try:
                created = datetime.strptime(created, "%Y-%m-%d")
                created = created.strftime('%Y-%m-%d')
            except:
                pass

        else :
            created = datetime.strptime(item['created_at'], "%Y-%m-%dT%XZ")
            created = created.strftime('%Y-%m-%d')
        text_file.write("     - " + created + "\n")

        # last updated, purely Github
        updated = datetime.strptime(item['updated_at'], "%Y-%m-%dT%XZ")
        text_file.write("     - " + updated.strftime('%Y-%m-%d') + "\n")

        # list of document links (urls comma-separated)
        maindoc = re.search('^Documentation: (.+?)\n', str(item['body']))
        if maindoc is not None:
            maindoc = maindoc.group(1)
            doc_list_formatted = ["`" + str(item['number']) + "-" + str(i) + " <" + x.strip() + ">`_" for i, x in enumerate(maindoc.split(','),1)]
            text_file.write("     - " + ', '.join(doc_list_formatted))
        else:
            text_file.write("     - ")
        text_file.write("\n")

        # author list, if missing just use Github issue creator
        author = re.search('^Author: (.+?)\n', str(item['body']), flags=re.MULTILINE)
        if author is not None:
            author_list_formatted = set()
            author_list = author.group(1)
            for a in author_list.split(","):
                authors.add(a.strip())
                author_list_formatted.add("`" + str(a.strip()) + "`_")
            text_file.write("     - " + ', '.join(author_list_formatted))
        else:
            author = "@" + item['user']['login']
            authors.add(author)
            text_file.write("     - `" + str(author) + "`_")
        text_file.write("\n")

        # shepherd (currnely only one)
        shepherd = re.search('Shepherd: (.+?)\n', str(item['body']))
        if shepherd is not None:
            authors.add(shepherd.group(1).strip())
            shepherd = "`" + shepherd.group(1).strip() + "`_"
        text_file.write("     - " + str(shepherd) + "\n")
    text_file.write("\n\n\n")

text_file.write("\n")

for author in authors:
    text_file.write("\n.. _" + author + ": https://github.com/" + author[1:])

text_file.close()
