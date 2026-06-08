import os
import re
import urllib.request
import xml.etree.ElementTree as ET
import html
from html.parser import HTMLParser

class RedditHTMLToMarkdown(HTMLParser):
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

def html_to_markdown(html_content):
    # Extract only the main body before "submitted by" section
    if '<!-- SC_ON -->' in html_content:
        html_content = html_content.split('<!-- SC_ON -->')[0]
    if '<!-- SC_OFF -->' in html_content:
        html_content = html_content.split('<!-- SC_OFF -->')[1]
    
    parser = RedditHTMLToMarkdown()
    parser.feed(html_content)
    text = ''.join(parser.markdown).strip()
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Standardize multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'[\s_]+', '_', name)
    return name.strip('_')[:100]

def main():
    feed_url = 'https://www.reddit.com/r/stocks/search.rss?q=flair:%22Company+Discussion%22&restrict_sr=1&sort=top&t=year'
    dest_dir = r'C:\Users\hppc\Desktop\CodePath'
    
    print(f"Fetching posts from Reddit RSS: {feed_url}")
    
    req = urllib.request.Request(
        feed_url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"Error fetching the RSS feed: {e}")
        return

    print("Parsing RSS feed...")
    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    # XML Namespaces
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    
    if not entries:
        print("No entries found in the RSS feed.")
        return

    print(f"Found {len(entries)} entries. Downloading up to 10...")
    
    os.makedirs(dest_dir, exist_ok=True)
    saved_count = 0
    
    for i, entry in enumerate(entries):
        if saved_count >= 10:
            break
            
        title = entry.find('atom:title', ns).text
        link_elem = entry.find('atom:link', ns)
        post_url = link_elem.attrib['href'] if link_elem is not None else "Unknown URL"
        
        # Author details
        author_elem = entry.find('atom:author', ns)
        author_name = "Unknown"
        if author_elem is not None:
            name_elem = author_elem.find('atom:name', ns)
            if name_elem is not None:
                author_name = name_elem.text.replace('/u/', '')
        
        # Date details
        published_elem = entry.find('atom:published', ns)
        published_date = published_elem.text if published_elem is not None else "Unknown Date"
        
        # Content body
        content_elem = entry.find('atom:content', ns)
        raw_html = content_elem.text if content_elem is not None else ""
        body_markdown = html_to_markdown(raw_html) if raw_html else "No content body."

        # Compile final file content
        file_content = f"""# {title}

- **Subreddit**: r/stocks
- **Flair**: Company Discussion
- **Author**: u/{author_name}
- **Date**: {published_date}
- **Source URL**: {post_url}

---

{body_markdown}
"""
        
        # Write to file
        safe_title = sanitize_filename(title)
        filename = f"{safe_title}.md"
        file_path = os.path.join(dest_dir, filename)
        
        print(f"[{saved_count+1}/10] Saving: {filename}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            saved_count += 1
        except Exception as e:
            print(f"Error saving file {filename}: {e}")

    print(f"Successfully saved {saved_count} posts to {dest_dir}!")

if __name__ == '__main__':
    main()
