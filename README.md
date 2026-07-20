## Data for the blog (not rendered/built)

* This is where I store all my data for the blog. For everyone's visibility and for my ease.
* This is deployed to [my blog](https://krshrimali.github.io) via https://github.com/krshrimali/krshrimali.github.io automatically using GitHub Actions!

## Theme Information

* The blog uses a small custom theme called **Typewriter** (`themes/typewriter`), built specifically for this blog — no external theme dependency or submodule required.
* Look and feel: plain, old-school, monospaced (Courier Prime for body text, Special Elite for headings), self-hosted webfonts, minimal chrome.
* Features include:
  * Light/dark toggle (button in the header, persisted in `localStorage`, defaults to the reader's system preference)
  * Responsive/mobile-friendly single-column layout
  * Self-hosted images (`static/assets/blogs`, `static/assets/cover-images`) — no dependency on external image hosts
  * Simple, dependency-free client-side search (`/search/`) over a generated `index.json`, no third-party JS libraries
  * Table of contents, tags/categories pages, RSS feed, previous/next post navigation
* Theme source: `themes/typewriter/layouts` (templates) and `themes/typewriter/static` (CSS/JS/fonts).

## Continuous Integration and Deployment

### PR Validation

The blog uses GitHub Actions to ensure that the website builds without errors before pull requests are merged to the main branch. This helps catch any issues early in the development process.

The PR validation workflow:
1. Automatically runs on every pull request to the main branch
2. Checks out the repository (the theme lives directly in `themes/typewriter`, no submodules needed)
3. Sets up Hugo with the latest version and extended support
4. Attempts to build the site with `hugo --minify`
5. Fails the check if the build process encounters any errors

This ensures that all PRs can be safely merged without breaking the site build.

### Automatic Deployment

The blog is automatically deployed to [krshrimali.github.io](https://krshrimali.github.io) whenever changes are pushed to the main branch, using GitHub Actions.

### Setting up the GitHub Actions workflows:

1. Create a Personal Access Token (PAT) with `repo` scope at [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Add the token as a repository secret named `PERSONAL_ACCESS_TOKEN` in the repository settings at [Settings > Secrets and variables > Actions](https://github.com/krshrimali/blog/settings/secrets/actions)

## Manual Compilation (if needed)

* Compile blog using: `hugo`. The rendered files will be stored in `public/` sub-folder.
* A script for manual deployment (if needed):
    ```bash
    hugo && cp -r public/* ../krshrimali.github.io/
    cd ../krshrimali.github.io && git add . && git commit -m "updates" && git push origin main
    ```
