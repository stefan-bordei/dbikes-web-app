## Contributor Git Workflow

1. Create a new branch:
`git branch <contributor_name>/<ticket_name>/<title>`
Example: `git branch stefanb/test/add-test-file`

2. Checkout the working branch
`git checkout <contributor_name>/<ticket_name>/<title>`

3. Do the cool work :)
4. Push your changes:
`git add <files>`
`git commit -m "<suggestive commit message>"`
`git push --set-upstream origin <contributor_name>/<ticket_name>/<title>`
5. Open a PR (Pull Request):
After pushing the new branch, you will see a message with a link for opening a new pull request:
```
remote: Create a pull request for 'sbordei/test/add-test-file' on GitHub by visiting:  
remote: https://github.com/stefan-bordei/dbikes-web-app/pull/new/sbordei/test/add-test-file
```
Visit the page, add a good description about the work you've done and the tests you've performed and create the PR.

6. Ask for 2 reviews
7. Once the changes are approved, merge to Main.

### Useful commands:
`git status` to check the branch you're on and the changes, if any.
Once you pushed your branch checkout main.
`git pull` pull latest changes from remote branch.
