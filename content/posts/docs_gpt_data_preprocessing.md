---
 author:
   name: "Kushashwa Ravi Shrimali"
 date: 2024-02-26
 linktitle: "Data Scrapping for ChatBot Model in Rust | DocsGPT | Part-2"
 title: "Data Scrapping for ChatBot Model in Rust | DocsGPT | Part-2"
 categories:
 - projects
 - rust
 tags:
 - project
 - deep learning
 - LLM
 - rust
 type:
 - post
 - posts
 weight: 10
 aliases:
 - /blog/docs-gpt-part-2/
 toc: false
 comments: true
---

Alright everyone, we are back. Just FYI, we've had a blog on introduction to DocsGPT before: https://krshrimali.github.io/posts/2024/02/building-a-chatbot-from-your-documentation-website-docsgpt/. This is a follow up blog where we'll discuss data scraping and preprocessing to be able to finetune our model for ChatBot use-case.

Quick recap?

1. Input is going to be a _single link to documentation page (index page)_.
2. Need to fetch data for "all the internal pages".
3. Preprocess (and/or clean) and transform the data to be able to finetune the model.
4. Finetune the model and use it for ChatBot use-case.

In this blog, we'll be covering the first two above, and the rest will be covered in the next blog(s).

## Data Scraping

The problem is simple, let's just define our function and it's return type. It kinda sets the tone.

```rust
pub fn fetch_data(input_link: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    // input_link is the link to the index page of the documentation concerned
}
```

Alright, so as it might be clear already, we'll be passing link to the index page of the documentation. For our use-case of PyTorch documentation, we'll use: https://pytorch.org/docs/stable/index.html. The return type is `Vec<String>` where each string is the content of the internal page.

This is an example function though, we'll be moving to another format as we go ahead. But for now, let's just keep it simple. There are 2 problems we're trying to solve here:

1. Fetch "all the internal pages" through the index page.
    - This includes going through all the hyperlinks in each page starting from the index page, and fetching the content of each page.
    - We'll include any external page (that is not internal to the documentation, for simplicity).
2. Getting content of the page

To be able to solve these problems, we'll use `soup` crate in Rust: https://docs.rs/soup/latest/soup/. For those who are used to using `beautifulsoup` in Python, it's pretty similar.

Let's start with the first problem. We'll define a function `extract_all_hyperlinks` which will take the index page link and return all the internal links. (the function won't be recursive)

Note that, to be able to do this, we'll just make sure to get the content of the index page first.

```rust
pub fn fetch_raw_html(main_html_link: String) -> Result<String, std::io::Error> {
    let output = reqwest::blocking::get(main_html_link).expect("Failed to fetch the URL");
    let output_text = output.text().expect("Failed to read the response text");
    Ok(output_text.to_string())
}

fn main() {
    let main_html_link: String = "https://pytorch.org/docs/stable/index.html".to_string();
    let raw_data: Result<String, std::io::Error> = fetch_raw_html(main_html_link.clone());

    env_logger::init();

    let mut all_links: Vec<String> = Vec::new();
    let mut all_text: Vec<String> = Vec::new();

    let if_succeeded = extract_all_hyperlinks(raw_data, &mut all_links, &mut all_text);
}
```

If you're wondering, why fetch raw HTML separately and then extract hyperlinks from the content? Rust is naturally a functional language, and following the practice to keep a single function limited to one single action, we're doing this. Will help testing efforts in the future.

Alright, so - so far, we got the raw HTML content (used `reqwest` crate for fetching the content), and then we're passing it to `extract_all_hyperlinks` function. The function will look something like this:

```rust
pub fn extract_all_hyperlinks(
    raw_data: Result<String, std::io::Error>,
    all_links: &mut Vec<String>,
    all_text: &mut Vec<String>,
) -> Result<(), std::io::Error> {
    match raw_data {
        Ok(content) => {
            let soup = Soup::new(&content);
            let text = soup.text();
            all_text.push(text);
            let all_tags_a_href = soup.tag("a").find_all();

            all_tags_a_href.enumerate().for_each(|(_, tag)| {
                let href = tag.get("href");
                match href {
                    Some(href) => {
                        // NOTE: Can you think of a better way to differentiate b/w internal and external links?
                        if href.starts_with("http")
                            || href.starts_with('_')
                            || href.starts_with('#')
                            || href.starts_with('.')
                        {
                            log::info!("Skipping: {:?}", href);
                            return;
                        }

                        all_links.push(href);
                    }
                    None => log::warn!("No href attribute found"),
                }
            });
            Ok(())
        }
        Err(e) => {
            log::error!("Error reading file: {:?}", e,);
            Err(e)
        }
    }
}
```

What are we doing here?

- We got the content from `fetch_raw_html`, if valid we'll create a `Soup` object from it and get the text.
- Once we have the text, we'll get all the `a` tags and their `href` attributes.
- We'll skip the external links (for simplicity) and add the internal links to `all_links` vector.
    - I'm open to ideas on differentiating b/w external and internal links. For now, anything that starts with `http`, `_`, `#`, or `.` is considered external (please note that `https` automatically comes in this because it's a superset of `http`).
- We'll also add the text to `all_text` vector.

It's comparatively easier to test these functions now, thanks to the original idea of keeping their jobs separate.

Alright, now we have the hyperlinks, but we haven't fetched all the content of those hyperlinks and their hyperlinks and their hyperlinks... (nested hyperlinks xD).

It's easy if you think about it:

1. Iterate through all the hyperlinks, for each link - get the data and store it.

^^ Hmm, sounds very easy, duh? Well, we are missing one part. What if the link is repeated? Which is quite possible in any documentation. Let's revise our list above:


1. Iterate through all the hyperlinks, for each link - get the data and store it.
2. If the link is already in a HashSet, skip it. Otherwise, add it to the HashSet and store the data.

Here's where we'll just re-use our functions defined above:

```rust
fn main() {
    // ...
    let mut visited_set: HashSet<String> = HashSet::new();

    for link in all_links.iter() {
        if visited_set.contains(link) {
            log::info!("Skipping link because it's alr visited: {:?}", link);
            continue;
        }

        // NOTE: Guess what we are doing here?
        let modified_link = Path::new(&main_html_link).parent().unwrap().join(link);
        let content = fetch_raw_html(modified_link.display().to_string());

        let success = extract_all_hyperlinks(content, &mut nested_links, &mut all_text);

        visited_set.insert(link.clone());

        if success.is_ok() {
            log::info!("Success for link: {:?}", link);
            log::debug!("Nested links: {:?}", nested_links);
        } else {
            log::info!("Failed for link: {:?}", link);
        }
    }
    // ...
}
```

If you saw the code above, there is a note which says:

> // NOTE: Guess what we are doing here?

Alright, so for any internal link, which would look like this: `/docs/stable/tensors.html`, we'll just join it with the parent link and fetch the content. This is a very simple way to do it, and it's not the best way to do it. But for now, it's good enough. Do note that, the parent link comes from the initial link the user passes to this flow, which was: `https://pytorch.org/docs/stable/index.html` in this case. So we'll just replace `/index.html` with `/docs/stable/tensors.html` and fetch the content.

Once this is done, the next task would be to understand what data we got - how we can transform it - what kind of cleaning methods are needed etc. That's going to be a good exercise for the next blog. For now, I think, this is a good start! Right? :)

## YouTube!

As always, a shameless plug, I do have a YouTube channel guys! Please consider referring to the channel if there's anything that interests you there. Here's the link: https://www.youtube.com/c/kushashwaraviShrimali.

## Discord!

Oh, and yes, we do have a discord channel. Please consider joining the channel for any discussions, or if you need any help. Here's the link: https://discord.gg/nh2KuAX3V8.

Alright then 🤝, I'll see you soon in the next blog. Thank you all, bye! ❤️
