# Git and GitHub for the Hackathon

A minimal, practical guide to using Git and GitHub for this workshop. You don't need to be a git expert — just enough to get the code, make changes, and share them back.

## What Git and GitHub Are

Git is a version control system that tracks changes to files on your machine. GitHub is a web platform that hosts Git repositories and adds collaboration features like pull requests, issues, and code review. The workshop code lives in GitHub repositories under the `ArkinLaboratory` organization.

## One-Time Setup

### Install Git

**macOS:** Git comes pre-installed. If not, run:
```bash
xcode-select --install
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install git
```

**Windows:** Download the installer from [git-scm.com](https://git-scm.com/download/win).

Verify the installation:
```bash
git --version
```

### Configure Your Identity

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@lbl.gov"
```

These settings attach your name and email to every commit you make. This is metadata about authorship, not authentication.

### Authenticate with GitHub

The GitHub CLI (`gh`) is the simplest way to authenticate.

**Install GitHub CLI:**

macOS:
```bash
brew install gh
```

Linux (Debian/Ubuntu):
```bash
sudo apt install gh
```

Windows: Download from [cli.github.com](https://cli.github.com/).

**Authenticate:**
```bash
gh auth login
```

Follow the prompts:
- Choose `GitHub.com`
- Choose `HTTPS` when asked about protocol
- Select `Login with a web browser`
- Authorize the GitHub CLI app in your browser

Verify authentication:
```bash
gh auth status
```

**Alternative:** If you prefer SSH keys, see [GitHub's SSH setup guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh). HTTPS with the GitHub CLI is simpler for most people.

## Getting the Code

### Clone a Repository

```bash
gh repo clone ArkinLaboratory/ai-skills-workshop
cd ai-skills-workshop
```

This creates a local copy of the repository on your machine. The `gh` command handles authentication automatically.

**Without the GitHub CLI:**
```bash
git clone https://github.com/ArkinLaboratory/ai-skills-workshop.git
cd ai-skills-workshop
```

Replace `ArkinLaboratory` with the actual organization name if different.

### Getting Updates

At the start of each session, pull the latest changes:

```bash
git pull
```

This fetches new commits from GitHub and updates your local copy.

## Making Changes

### The Basic Workflow

Edit files in your local repository, then move them through three stages:

```
Working directory → Staging area → Commit → Push → (optionally) Pull Request
```

**Working directory:** Your actual files on disk.
**Staging area:** Files you've marked for the next commit.
**Commit:** A snapshot of your changes, saved locally with a message.
**Push:** Send your commits to GitHub.

### Check What Changed

```bash
git status
```

Shows which files are modified, new, or staged.

```bash
git diff
```

Shows the exact line-by-line changes you've made (before staging).

```bash
git diff --staged
```

Shows changes you've already staged.

### Stage and Commit

Stage specific files:
```bash
git add file1.py file2.md
```

Or stage everything:
```bash
git add .
```

Then commit:
```bash
git commit -m "Add PaperBLAST rate limiting"
```

**Commit messages should be clear:** describe what you changed and why in one or two sentences. Examples:
- `"Fix check_deps.py for Apple Silicon"`
- `"Add GapMind tutorial with common organisms"`
- `"Increase timeout in fetch_sequence_data to 60s"`

### Push to GitHub

```bash
git push
```

Sends your commits to GitHub so others can see them.

## Working with Branches

### Why Branches?

Branches let you work on changes without affecting the main codebase. The main branch stays stable while you experiment on your own branch. This is standard practice when multiple people are editing.

### Create and Switch to a Branch

```bash
git checkout -b my-feature-name
```

Use descriptive branch names:
- `add-gapmind-tutorial`
- `fix-check-deps`
- `paperblast-rate-limit`
- `improve-error-messages`

### See Your Current Branch

```bash
git branch
```

The branch with an asterisk is your current branch.

### Push a Branch

```bash
git push -u origin my-feature-name
```

The `-u` flag sets up tracking, so future `git push` commands work without specifying the branch name.

### Switch Back to Main

```bash
git checkout main
git pull
```

## Pull Requests

### What Is a Pull Request?

A pull request (PR) is a proposal to merge your branch into the main branch. It shows your changes, lets others review and comment, and creates a permanent record of what changed and why. This is the standard way to contribute to a shared project.

### Create a Pull Request

After pushing your branch, create a PR:

```bash
gh pr create --title "Add GapMind tutorial" --body "Adds a step-by-step tutorial for using GapMind with common organisms."
```

**Or manually:** Push your branch to GitHub, then go to the repository's web page. GitHub will show a prompt to create a PR from your branch.

### Review and Merge

The repository maintainer (or whoever maintains the branch) will:
1. Review your code
2. Comment or request changes
3. Merge the PR into main

During the hackathon, PRs may be merged quickly or you may have permission to merge your own. If changes are requested, make them locally, commit, and push — the PR updates automatically.

### Close and Delete a Branch

Once merged, delete the branch locally:

```bash
git checkout main
git pull
git branch -d my-feature-name
```

## GitHub Issues

### What Are Issues?

Issues are tasks, bugs, or feature requests tracked in the repository. During the hackathon, issues represent work items you can claim. Each has a number, title, description, assignee, and labels.

### Finding Issues to Work On

1. Go to the repository on GitHub
2. Click the **Issues** tab
3. Look for labels like `good-first-issue`, `help-wanted`, or `hackathon`
4. Click an issue to see details
5. Leave a comment claiming it, or use the **Assignees** section to assign it to yourself

### Creating Issues

```bash
gh issue create --title "Bug: check_deps.py fails on Apple Silicon" --body "The lxml installation fails on M1/M2 Macs when running setup.sh..."
```

Or use the GitHub web UI: Issues tab → **New Issue**.

### Linking Issues to PRs

In your PR description or a commit message, reference the issue:

```bash
git commit -m "Fix check_deps.py for Apple Silicon. Fixes #42"
```

When the PR is merged, issue #42 closes automatically. Use `Fixes #<number>`, `Resolves #<number>`, or `Closes #<number>`.

## Common Problems

### "I made changes on main and can't push"

You may have pulled someone else's changes. Stash yours, pull, and re-apply:

```bash
git stash
git pull
git stash pop
```

If there are conflicts (same lines edited by you and someone else), resolve them manually, then:

```bash
git add .
git commit -m "Resolve merge conflict"
git push
```

### "I'm on the wrong branch"

Stash changes, switch branches, and re-apply:

```bash
git stash
git checkout correct-branch-name
git stash pop
```

### "I have merge conflicts"

Conflicts occur when two people edit the same lines. Git marks them:

```
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> their-branch
```

Edit the file to keep what you want, remove the `<<<<<<<`, `=======`, and `>>>>>>>` markers, then:

```bash
git add conflicted-file.py
git commit -m "Resolve merge conflict"
git push
```

### "I accidentally committed something I shouldn't have"

Undo the last commit but keep your changes staged:

```bash
git reset --soft HEAD~1
```

Then edit files and re-commit. **Don't use `--hard`** unless you want to lose changes entirely.

### "I want to see what I changed in an old commit"

```bash
git log --oneline
```

Shows recent commits with their IDs and messages. Then:

```bash
git show <commit-id>
```

Displays the changes in that commit.

## Quick Reference

| Task | Command |
|------|---------|
| Clone a repository | `gh repo clone ArkinLaboratory/repo-name` |
| Check status | `git status` |
| See changes | `git diff` |
| Stage files | `git add file1 file2` |
| Commit | `git commit -m "message"` |
| Push | `git push` |
| Pull latest | `git pull` |
| Create a branch | `git checkout -b branch-name` |
| Switch branches | `git checkout branch-name` |
| Push a new branch | `git push -u origin branch-name` |
| List branches | `git branch` |
| Delete a branch | `git branch -d branch-name` |
| Create pull request | `gh pr create --title "..." --body "..."` |
| List pull requests | `gh pr list` |
| Create an issue | `gh issue create --title "..." --body "..."` |
| List issues | `gh issue list` |
| View commit history | `git log --oneline` |
| Undo last commit | `git reset --soft HEAD~1` |

## Further Reading

- [Git Handbook (GitHub)](https://docs.github.com/en/get-started/using-git/about-git)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Pro Git Book](https://git-scm.com/book/en/v2) (free, comprehensive)
