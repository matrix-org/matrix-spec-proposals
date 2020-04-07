#!/usr/bin/env python
#
# proposals.py: generate an RST file (proposals.rst) from queries to github.com/matrix.org/matrix-doc/issues.

import requests
import re
from datetime import datetime

# a list of the labels we care about
LABELS_LIST=[
    'proposal-in-review',
    'proposed-final-comment-period',
    'final-comment-period',
    'finished-final-comment-period',
    'spec-pr-missing',
    'spec-pr-in-review',
    'merged',
    'proposal-postponed',
    'abandoned',
    'obsolete',
]


authors = set()
prs = set()

def getpage(url):
    """Request the given URL, and extract the pagecount from the response headers

    Args:
        url (str): URL to fetch

    Returns:
        Tuple[int, list]: number of pages, and the list of items on this page
    """
    resp = requests.get(url)

    pagecount = 1
    for link in resp.links.values():
        if link['rel'] == 'last':
            pagecount = int(re.search('page=(.+)', link['url']).group(1))

    val = resp.json()
    if not isinstance(val, list):
        print(val) # Just dump the raw (likely error) response to the log
        raise Exception("Error calling %s" % url)
    return (pagecount, val)

def getbylabel(label):
    """Fetch all the issues with a given label

    Args:
        label (str): label to fetch

    Returns:
        Iterator[dict]: an iterator over the issue list.
    """
    urlbase = 'https://api.github.com/repos/matrix-org/matrix-doc/issues?state=all&labels=' + label + '&page='
    page = 1
    while True:
        (pagecount, results) = getpage(urlbase + str(page))
        for i in results:
            yield i
        page += 1
        if page > pagecount:
            return

def print_issue_list(text_file, label, issues):
    text_file.write(label + "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if (len(issues) == 0):
        text_file.write("No proposals.\n\n")
        return

    text_file.write(".. list-table::\n   :header-rows: 1\n   :widths: auto\n   :stub-columns: 1\n\n")
    text_file.write("   * - MSC\n")
    text_file.write("     - Proposal Title\n")
    text_file.write("     - Creation Date\n")
    text_file.write("     - Update Date\n")
    text_file.write("     - Documentation\n")
    text_file.write("     - Author\n")
    text_file.write("     - Shepherd\n")
    text_file.write("     - PRs\n")

    for item in issues:
        # set the created date, find local field, otherwise Github
        body = str(item['body'])
        created = re.search('^Date: (.+?)\n', body, flags=re.MULTILINE)
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
        item['created'] = created

    issues_to_print = sorted(issues, key=lambda issue_sort: issue_sort["created"])

    for item in issues_to_print:
        # MSC number
        text_file.write("   * - `MSC" + str(item['number']) + " <" + item['html_url'] + ">`_\n")

        # title from Github issue
        text_file.write("     - " + item['title'] + "\n")

        # created date
        text_file.write("     - " + item['created'] + "\n")

        # last updated, purely Github
        updated = datetime.strptime(item['updated_at'], "%Y-%m-%dT%XZ")
        text_file.write("     - " + updated.strftime('%Y-%m-%d') + "\n")

        # list of document links (urls comma-separated)
        maindoc = re.search('^Documentation: (.+?)$', str(item['body']), flags=re.MULTILINE)
        if maindoc is not None:
            maindoc = maindoc.group(1)
            doc_list_formatted = ["`" + str(item['number']) + "-" + str(i) + " <" + x.strip() + ">`_" for i, x in enumerate(maindoc.split(','),1)]
            text_file.write("     - " + ', '.join(doc_list_formatted))
        else:
            text_file.write("     - ")
        text_file.write("\n")

        # author list, if missing just use Github issue creator
        author = re.search('^Author: (.+?)$', str(item['body']), flags=re.MULTILINE)
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

        # shepherd (currently only one)
        shepherd = re.search('Shepherd: (.+?)\n', str(item['body']))
        if shepherd is not None:
            authors.add(shepherd.group(1).strip())
            shepherd = "`" + shepherd.group(1).strip() + "`_"
        text_file.write("     - " + str(shepherd) + "\n")

        # PRs
        try:
            pr_list = re.search('PRs: (.+?)$', str(item['body']))
            if pr_list is not None:
                pr_list_formatted = set()
                pr_list = pr_list.group(1)
                for p in pr_list.split(","):
                    if re.match(r"#\d", p.strip()):
                        prs.add(p.strip())
                        pr_list_formatted.add("`PR" + str(p.strip()) + "`_")
                    elif re.match(r"https://github.com/matrix-org/matrix-doc/pulls/\d", p.strip()):
                        pr = "#" + p.strip().replace('https://github.com/matrix-org/matrix-doc/pulls/', '')
                        prs.add(pr)
                        pr_list_formatted.add("`PR" + str(pr) + "`_")
                    else:
                        raise RuntimeWarning
                text_file.write("     - " + ', '.join(pr_list_formatted))
                text_file.write("\n")
            else:
                text_file.write("     - \n")
        except:
            print("exception parsing PRs for MSC" + str(item['number']))
            text_file.write("     - \n")

    text_file.write("\n\n\n")


# first get all of the issues, filtering by label
issues = {n: [] for n in LABELS_LIST}
# use the magic 'None' key for a proposal in progress
issues[None] = []

for prop in getbylabel('proposal'):
    print("%s: %s" % (prop['number'], [l['name'] for l in prop['labels']]))
    found_label = False
    for label in prop['labels']:
        label_name = label['name']
        if label_name in issues:
            issues[label_name].append(prop)
            found_label = True

    # if it doesn't have any other label, assume it's work-in-progress
    if not found_label:
        issues[None].append(prop)

text_file = open("specification/proposals.rst", "w")

text_file.write("Tables of Tracked Proposals\n---------------------------\n\n")

print_issue_list(text_file, "<work-in-progress>", issues[None])
for label in LABELS_LIST:
    print_issue_list(text_file, label, issues[label])

text_file.write("\n")

for author in authors:
    text_file.write("\n.. _" + author + ": https://github.com/" + author[1:])

for pr in prs:
    text_file.write("\n.. _PR" + pr + ": https://github.com/matrix-org/matrix-doc/pull/" + pr.replace('#', ''))

text_file.close()
