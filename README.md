## Data for the blog (not rendered/built)

* This is where I store all my data for the blog. For everyone's visiblity and for my ease.
* This is deployed to [my blog](https://krshrimali.github.io) via https://github.com/krshrimali/krshrimali.github.io, manually! :D (one day - maybe GitHub Actions)

## Instructions on compiling the blog

* Compile blog using: `hugo`. The rendered files will be stored in `public/` sub-folder. Copy it to `krshrimali.github.io` repository and push, that's it.
* A n00bish script for this: (very personalized)
    ```bash
    hugo && cp -r public/* ../krshrimali.github.io/
    cd ../krshrimali.github.io && git add . && git commit -m "updates" && git push origin main
    ```
