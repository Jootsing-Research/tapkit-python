---
name: release
description: Bump version, commit, tag, and push to trigger a PyPI release
argument-hint: "<version>"
---

Release a new version of the tapkit package to PyPI.

## Usage

- `/release <version>` — release a specific version, e.g., `/release 0.2.0`
- `/release` — auto-increment the patch version and confirm with the user before proceeding

## Steps

1. **Ensure you're on `master`**: Check the current branch. If not on `master`, switch to it and pull latest.

2. **Pull latest**: Run `git pull origin master` to make sure you're up to date.

3. **Read the current version** from the `version` field in `pyproject.toml`.

4. **Determine the next version**:
   - If the user provided a version argument, use that.
   - If no version was provided, auto-increment the **patch** number (e.g., `0.1.4` → `0.1.5`). The version format is `major.minor.patch`.

5. **Confirm with the user**: Show the current version and the proposed next version, and ask the user to confirm before proceeding. For example: "Current version is 0.1.4. Release 0.1.5? (y/n)". Wait for confirmation before continuing.

6. **Bump the version**: Update the `version` field in `pyproject.toml` to the new version.

7. **Commit**: Stage `pyproject.toml` and commit with the message `Bump version to <version>`.

8. **Tag**: Create a git tag `v<version>` (prefixed with `v`).

9. **Push**: Push the commit and tag to origin:
   ```bash
   git push origin master
   git push origin v<version>
   ```

10. **Confirm**: Let the user know the release has been pushed and the GitHub Action will publish to PyPI.

## Important

- The version argument should NOT include a `v` prefix — just the number (e.g., `0.1.5`, not `v0.1.5`).
- If the user provides a `v` prefix, strip it before updating `pyproject.toml` but include it in the git tag.
- Always confirm the current version and proposed new version with the user before making any changes.
