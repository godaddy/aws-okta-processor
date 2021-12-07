# Maintainer Publishing Steps
1. Squash and merge PR after unit tests pass and approvals then delete the branch.
2. Using an IDE pull in head of remote master branch to local.
3. Increment version stored in [`aws_okta_processor/__init__.py`](aws_okta_processor/__init__.py). Use the latest semantic versioning standard found [here](https://semver.org/) as a guide.
4. Commit version change to local master branch then push to remote with `git push origin master`.
5. Create a tag matching current version and annotate with attributed changes:
   ```
   git tag -a v<VERSION>
   
   - @person did x y z
   ```
6. Push tag to remote with `git push origin v<VERSION>`.