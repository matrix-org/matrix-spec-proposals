"use strict";

/**
 * This Node script fetches MSC proposals and stores them in /data/msc,
 * so they can be used by a Hugo template to render summary tables of them
 * in the specification.
 *
 * In detail, it:
 * - fetches all GitHub issues from matrix-doc that have the `proposal` label
 * - groups them by their state in the MSC process
 * - does some light massaging of them so it's easier for the Hugo template to work with them
 * - store them at /data/msc
 */

// built-in modules
const path = require('path');
const fs = require('fs');

// third-party modules
const fetch = require('node-fetch');

// We will write proposals into the /data/msc directory
const outputDir = path.join(__dirname, "../data/msc");

/**
 * This defines the different proposal lifecycle states.
 * Each state has:
 * - `label`: a GitHub label used to identify issues in this state
 * - `title`: used for things like headings in renderings of the proposals
 */
const states = [
  {
    label: "proposal-in-review",
    title: "Proposal In Review"
  },
  {
    label: "proposed-final-comment-period",
    title: "Proposed Final Comment Period"
  },
  {
    label: "final-comment-period",
    title: "Final Comment Period"
  },
  {
    label: "finished-final-comment-period",
    title: "Finished Final Comment Period"
  },
  {
    label: "spec-pr-missing",
    title: "Spec PR Missing"
  },
  {
    label: "spec-pr-in-review",
    title: "Spec PR In Review"
  },
  {
    label: "merged",
    title: "Merged"
  },
  {
    label: "proposal-postponed",
    title: "Postponed"
  },
  {
    label: "abandoned",
    title: "Abandoned"
  },
  {
    label: "obsolete",
    title: "Obsolete"
  }
];

let issues = [];

/**
 * Fetch all the MSC proposals from GitHub.
 *
 * GitHub only lets us fetch 100 items at a time, and it gives us a `link`
 * response header containing the URL for the next batch.
 * So we will keep fetching until the response doesn't contain the "next" link.
 */
async function getIssues() {

  /**
   * A pretty ugly function to get us the "next" link in the header if there
   * was one, or `null` otherwise.
   */
  function getNextLink(header) {
    const links = header.split(",");
    for (const link of links) {
      const linkPieces = link.split(";");
      if (linkPieces[1] == ` rel=\"next\"`) {
        const next = linkPieces[0].trim();
        return next.substring(1, next.length-1);
      }
    }
    return null;
  }

  let pageLink = "https://api.github.com/repos/matrix-org/matrix-doc/issues?state=all&labels=proposal&per_page=100";
  while (pageLink) {
    const response = await fetch(pageLink);
    const issuesForPage = await response.json();
    issues = issues.concat(issuesForPage);
    const linkHeader = response.headers.get("link");
    pageLink = getNextLink(linkHeader);
  }
}

getIssues().then(processIssues);

/**
 * Rather than just store the complete issue, we'll extract
 * only the pieces we need.
 * We'll also do some transformation of the issues, just because
 * it's easier to do in JS than in the template.
 */
function getProposalFromIssue(issue) {

  /**
   * A helper function to fetch the contents of special
   * directives in the issue body.
   * Looks for a directive in the format:
   * `^${directiveName}: (.+?)$`, returning the matched
   *  part or null if the directive wasn't found.
   */
  function getDirective(directiveName, issue) {
    const re = new RegExp(`^${directiveName}: (.+?)$`, "m");
    const found = issue.body?.match(re);
    return found? found[1]: null;
  }

  function getDocumentation(issue) {
    const found = getDirective("Documentation", issue);
    if (found) {
      return found.split(",").map(a => a.trim());
    } else {
      return [];
    }
  }

  function getAuthors(issue) {
    const found = getDirective("Author", issue);
    if (found) {
      return found.split(",").map(a => a.trim().substr(1));
    } else {
      return [`${issue.user.login}`];
    }
  }

  function getShepherd(issue) {
    const found = getDirective("Shepherd", issue);
    if (found) {
      return found.substr(1);
    } else {
      return null;
    }
  }

  return {
    number: issue.number,
    url: issue.html_url,
    title: issue.title,
    created_at: issue.created_at.substr(0, 10),
    updated_at: issue.updated_at.substr(0, 10),
    authors: getAuthors(issue),
    shepherd: getShepherd(issue),
    documentation: getDocumentation(issue)
  }
}

/**
 * Returns the intersection of two arrays.
 */
function intersection(array1, array2) {
  return array1.filter(i => array2.includes(i));
}

/**
 * Given all the GitHub issues with a "proposal" label:
 * - group issues by the state they are in, and for each group:
 *     - extract the bits we need from each issue
 *     - write the result under /data/msc
 */
function processIssues()  {
  if (!fs.existsSync(outputDir)){
    fs.mkdirSync(outputDir);
  }
  const output = [];
  // make a group of "work in progress" proposals,
  // which are identified by not having any of the state labels
  const stateLabels = states.map(s => s.label);
  const worksInProgress = issues.filter(issue => {
    const labelsForIssue = issue.labels.map(l => l.name);
    return intersection(labelsForIssue, stateLabels).length === 0;
  });
  output.push({
    title: "Work In Progress",
    label: "work-in-progress",
    proposals: worksInProgress.map(issue => getProposalFromIssue(issue))
  });
  // for each defined state
  for (const state of states) {
    // get the set of issues for that state
    const issuesForState = issues.filter(msc => {
      return msc.labels.some(l => l.name === state.label);
    });
    // store it in /data
    output.push({
      title: state.title,
      label: state.label,
      proposals: issuesForState.map(issue => getProposalFromIssue(issue))
    });
  }
  const outputData = JSON.stringify(output, null, '\t');
  const outputFile = path.join(outputDir, `proposals.json`);
  fs.writeFileSync(outputFile, outputData);
}
