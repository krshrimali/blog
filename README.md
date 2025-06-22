## Data for the blog (not rendered/built)

* This is where I store all my data for the blog. For everyone's visibility and for my ease.
* This is deployed to [my blog](https://krshrimali.github.io) via https://github.com/krshrimali/krshrimali.github.io automatically using GitHub Actions!

## Theme Information

* The blog uses the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme - a simple, fast, and developer-friendly theme.
* The theme is included as a Git submodule. When cloning this repository, use `git clone --recurse-submodules` to ensure the theme is included.
* Features include:
  * Light/dark mode toggle (automatically adapts to user's system preferences by default)
  * Responsive design optimized for all device sizes
  * Clean, readable typography
  * The homepage immediately displays recent blog posts for better user experience
  * Fast loading times and optimized performance
  * Search functionality to find blog posts by content or title

## Continuous Integration and Deployment

### PR Validation

The blog uses GitHub Actions to ensure that the website builds without errors before pull requests are merged to the main branch. This helps catch any issues early in the development process.

The PR validation workflow:
1. Automatically runs on every pull request to the main branch
2. Checks out the repository with all submodules (ensuring themes are properly included)
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
