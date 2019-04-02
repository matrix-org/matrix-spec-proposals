# How to release a specification

There are several specifications that belong to matrix, such as the client-server
specification, server-server specification, and identity service specification. Each
of these gets released independently of each other with their own version numbers.

Once a specification is ready for release, a branch should be created to track the
changes in and to hold potential future hotfixes. This should be the name of the
specification (as it appears in the directory structure of this project) followed
by "release-" and the release version. For example, if the Client-Server Specification
was getting an r0.4.0 release, the branch name would be `client_server/release-r0.4.0`.

*Note*: Historical releases prior to this process may or may not have an appropriate
release branch. Releases after this document came into place will have an appropriate
branch.

The remainder of the process is as follows:
1. Activate your Python 3 virtual environment.
1. Having checked out the new release branch, navigate your way over to `./changelogs`.
1. Follow the release instructions provided in the README.md located there.
1. Update any version/link references across all specifications.
1. Generate the specification using `./scripts/gendoc.py`, specifying all the
   API versions at the time of generation. For example: `./scripts/gendoc.py -c r0.4.0 -s r0.1.0 -i r0.1.0 #etc`
1. PR the changes to the matrix-org/matrix.org repository (for historic tracking).
   * This is done by making a PR to the `unstyled_docs/spec` folder for the version and
     specification you're releasing.
   * Don't forget to symlink the new release as `latest`.
   * For the client-server API, don't forget to generate the swagger JSON by using
     `./scripts/dump-swagger.py -c r0.4.0`. This will also need symlinking to `latest`.
1. Commit the changes and PR them to master. **Wait for review from the spec core team.**
   * Link to your matrix-org/matrix.org so both can be reviewed at the same time.
1. Tag the release with the format `client_server/r0.4.0`.
1. Perform a release on GitHub to tag the release.
1. Yell from the mountaintop to the world about the new release.

### Creating a release for a brand-new specification

Some specifications may not have ever had a release, and therefore need a bit more work
to become ready.

1. Activate your Python 3 virtual environment.
1. Having checked out the new release branch, navigate your way over to `./changelogs`.
1. Follow the "new changelog" instructions provided in the README.md located there.
1. Open the specification RST file and make some changes:
   * Using a released specification as a template, update the changelog section.
   * Use the appropriate changelog variable in the RST.
1. Create/define the appropriate variables in `gendoc.py`.
1. Update `targets.yml`.
1. Update any version/link references across all specifications.
1. Follow the regular release process.
