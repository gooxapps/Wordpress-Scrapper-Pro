import json
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET

def escape_xml(text):
    if not text: return ""
    return f"<![CDATA[{text}]]>"

def generate_wxr(results_file, output_file):
    if not os.path.exists(results_file):
        print(f"File not found: {results_file}")
        return

    with open(results_file, 'r') as f:
        items = json.load(f)

    wxr_header = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
	xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:wp="http://wordpress.org/export/1.2/"
>
<channel>
	<title>Goox Scraper Export</title>
	<link>http://localhost</link>
	<description>Automated Scraper Export</description>
	<pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
	<language>en-US</language>
	<wp:wxr_version>1.2</wp:wxr_version>
"""

    wxr_items = ""
    for i, item in enumerate(items):
        title = item.get('title', 'No Title')
        content = item.get('description_html', '')
        # Add download links to the end of content
        mirrors = item.get('mirrors', [])
        if mirrors:
            content += "<h3>Download Mirrors</h3><ul>"
            for link in mirrors:
                content += f'<li><a href="{link}" target="_blank">Download from {link.split("/")[2]}</a></li>'
            content += "</ul>"
            
        if item.get('preview_url'):
            content += f'<p><a href="{item.get("preview_url")}" class="button" target="_blank">Live Demo</a></p>'
        
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        post_id = 10000 + i
        
        wxr_items += f"""
	<item>
		<title>{title}</title>
		<link>http://localhost/{slug}</link>
		<pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
		<dc:creator><![CDATA[admin]]></dc:creator>
		<guid isPermaLink="false">http://localhost/?p={post_id}</guid>
		<description></description>
		<content:encoded><![CDATA[{content}]]></content:encoded>
		<excerpt:encoded><![CDATA[]]></excerpt:encoded>
		<wp:post_id>{post_id}</wp:post_id>
		<wp:post_date><![CDATA[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]]></wp:post_date>
		<wp:comment_status><![CDATA[open]]></wp:comment_status>
		<wp:ping_status><![CDATA[open]]></wp:ping_status>
		<wp:post_name><![CDATA[{slug}]]></wp:post_name>
		<wp:status><![CDATA[publish]]></wp:status>
		<wp:post_parent>0</wp:post_parent>
		<wp:menu_order>0</wp:menu_order>
		<wp:post_type><![CDATA[post]]></wp:post_type>
		<wp:post_password><![CDATA[]]></wp:post_password>
		<wp:is_sticky>0</wp:is_sticky>
		<category domain="category" nicename="{item.get('category', 'Uncategorized').lower().replace(' ', '-')}"><![CDATA[{item.get('category', 'Uncategorized')}]]></category>
	</item>"""

    wxr_footer = """
</channel>
</rss>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(wxr_header + wxr_items + wxr_footer)
    
    print(f"✅ WordPress WXR generated: {output_file}")

if __name__ == "__main__":
    import sys
    # Example: python3 wp_sync_wxr.py data/results_nullphp.json wordpress_export.xml
    if len(sys.argv) > 2:
        generate_wxr(sys.argv[1], sys.argv[2])
    else:
        # Default run
        generate_wxr("data/results_nullphp.json", "data/nullphp_export.xml")
        generate_wxr("data/results.json", "data/nulledscripts_export.xml")
