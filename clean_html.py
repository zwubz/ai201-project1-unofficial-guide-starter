import os
import re
import html
from html.parser import HTMLParser

class RedditHTMLBodyParser(HTMLParser):
    """
    Parses clean text and basic formatting from a selected Reddit post body HTML container.
    """
    def __init__(self):
        super().__init__()
        self.markdown = []
        self.in_link = False
        self.link_url = ""
        self.list_depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'p':
            self.markdown.append('\n\n')
        elif tag == 'br':
            self.markdown.append('\n')
        elif tag == 'a':
            self.in_link = True
            self.link_url = attrs_dict.get('href', '')
            self.markdown.append('[')
        elif tag in ('strong', 'b'):
            self.markdown.append('**')
        elif tag in ('em', 'i'):
            self.markdown.append('*')
        elif tag == 'code':
            self.markdown.append('`')
        elif tag == 'pre':
            self.markdown.append('\n```\n')
        elif tag in ('ul', 'ol'):
            self.list_depth += 1
            self.markdown.append('\n')
        elif tag == 'li':
            self.markdown.append('\n' + '  ' * (self.list_depth - 1) + '- ')
        elif tag == 'blockquote':
            self.markdown.append('\n> ')

    def handle_endtag(self, tag):
        if tag == 'p':
            pass
        elif tag == 'a':
            self.in_link = False
            self.markdown.append(f']({self.link_url})')
        elif tag in ('strong', 'b'):
            self.markdown.append('**')
        elif tag in ('em', 'i'):
            self.markdown.append('*')
        elif tag == 'code':
            self.markdown.append('`')
        elif tag == 'pre':
            self.markdown.append('\n```\n')
        elif tag in ('ul', 'ol'):
            self.list_depth -= 1
        elif tag == 'blockquote':
            self.markdown.append('\n')

    def handle_data(self, data):
        self.markdown.append(data)

def extract_meta_tags(html_content):
    """
    Parses OpenGraph and HTML meta tags to retrieve post metadata.
    """
    metadata = {
        'title': 'Unknown Title',
        'author': 'Unknown Author',
        'url': 'Unknown URL',
        'date': 'Unknown Date'
    }
    
    # 1. Extract Title
    title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html_content)
    if not title_match:
        title_match = re.search(r'<title>([^<]+)</title>', html_content)
    if title_match:
        metadata['title'] = html.unescape(title_match.group(1).replace(' : stocks', '').replace(' - Reddit', '').strip())
        
    # 2. Extract Source URL
    url_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html_content)
    if not url_match:
        url_match = re.search(r'<meta\s+property="og:url"\s+content="([^"]+)"', html_content)
    if url_match:
        metadata['url'] = url_match.group(1).strip()
        
    # 3. Extract Author
    author_match = re.search(r'<meta\s+name="twitter:creator"\s+content="([^"]+)"', html_content)
    if not author_match:
        # Fallback to looking for u/username in standard description strings
        desc_match = re.search(r'submitted\s+by\s+u/([\w-]+)', html_content)
        if desc_match:
            metadata['author'] = desc_match.group(1)
    if author_match:
        metadata['author'] = author_match.group(1).replace('@', '').replace('u/', '').strip()
        
    # 4. Extract Date
    date_match = re.search(r'<time\s+datetime="([^"]+)"', html_content)
    if date_match:
        metadata['date'] = date_match.group(1).strip()
        
    return metadata

def extract_body_content(html_content):
    """
    Locates the main post body text in the Reddit HTML page and cleans it.
    Usually located inside <div class="md"> or <div data-click-id="text_content">.
    """
    # Look for the primary <div class="md"> container representing the main post.
    # We find the post body container by locating '<div class="md"' but avoiding comments.
    # Shreddit or modern reddit pages put the main post text inside specific containers:
    body_html = ""
    
    # Strategy A: Find the post content container class in modern Reddit (e.g. shreddit-post or post-rtjson-content)
    rtjson_match = re.search(r'<div\s+id="[^"]*-post-rtjson-content"[^>]*>(.*?)</div>\s*</shreddit-post>', html_content, re.DOTALL)
    if rtjson_match:
        body_html = rtjson_match.group(1)
    
    # Strategy B: Find classic <div class="md"> inside the main post body
    if not body_html:
        md_divs = re.findall(r'<div\s+class="md"[^>]*>(.*?)</div>', html_content, re.DOTALL)
        if md_divs:
            # Usually the first md class div belongs to the main post body
            body_html = md_divs[0]
            
    # Strategy C: Look for shreddit-post body
    if not body_html:
        shreddit_match = re.search(r'<shreddit-post[^>]*>(.*?)</shreddit-post>', html_content, re.DOTALL)
        if shreddit_match:
            body_html = shreddit_match.group(1)
            
    if not body_html:
        return "No body content found in raw HTML."
        
    # Clean up standard styling script and nested comment elements if they bled in
    body_html = re.sub(r'<script.*?>.*?</script>', '', body_html, flags=re.DOTALL)
    
    # Parse HTML structure to clean Markdown text
    parser = RedditHTMLBodyParser()
    parser.feed(body_html)
    markdown_text = ''.join(parser.markdown).strip()
    
    # Normalize excessive newlines
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    return html.unescape(markdown_text)

def clean_reddit_html(html_filepath, output_dir):
    """
    Reads a raw Reddit HTML file, cleans it, extracts metadata,
    and writes it as a formatted Markdown file.
    """
    filename = os.path.basename(html_filepath)
    print(f"Processing raw HTML file: {filename}")
    
    try:
        with open(html_filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None
        
    metadata = extract_meta_tags(html_content)
    body_markdown = extract_body_content(html_content)
    
    # Create clean Markdown file content
    markdown_content = f"""# {metadata['title']}

- **Subreddit**: r/stocks
- **Flair**: Company Discussion
- **Author**: u/{metadata['author']}
- **Date**: {metadata['date']}
- **Source URL**: {metadata['url']}

---

{body_markdown}
"""
    
    # Sanitize and write
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', metadata['title'])
    safe_title = re.sub(r'[\s_]+', '_', safe_title).strip('_')[:100]
    
    out_filename = f"{safe_title}.md"
    out_filepath = os.path.join(output_dir, out_filename)
    
    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    print(f"Successfully cleaned HTML and saved Markdown: {out_filename}")
    return out_filepath

def main():
    # Example usage:
    # If a user had downloaded HTML pages in C:\Users\hppc\Desktop\CodePath\raw_html\
    # this script would clean them and output markdown files to C:\Users\hppc\Desktop\CodePath\
    raw_html_dir = r'C:\Users\hppc\Desktop\CodePath\raw_html'
    output_dir = r'C:\Users\hppc\Desktop\CodePath'
    
    if not os.path.exists(raw_html_dir):
        print(f"Note: Raw HTML folder '{raw_html_dir}' not found. Create it to run HTML cleaning on files.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(raw_html_dir):
        if filename.endswith('.html') or filename.endswith('.htm'):
            filepath = os.path.join(raw_html_dir, filename)
            clean_reddit_html(filepath, output_dir)

if __name__ == '__main__':
    main()
