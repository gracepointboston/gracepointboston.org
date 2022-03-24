#!/usr/bin/env python3

import os
import re
import subprocess

domain = "www.gracepointboston.org"
os.makedirs(domain, exist_ok=True)

curl_process = subprocess.run(["curl", "https://" + domain], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
html = curl_process.stdout

######################################################################
# Head
######################################################################
print("Processing: header_injection.html")
head = html.split("<head>")[1].split("</head>")[0]
head = re.sub("^[^>]*>", "", head.split("site.css")[1]) # Cut off everything before the site.css link
head = head.split("<!--")[0] # Strip off SS-generated comment at the end of our header
head = head.strip() + "\n"
open(domain + "/header_injection.html", "w").write(head)

######################################################################
# Footer
######################################################################
print("Processing: footer_injection.html")
footer = html.split("site-bundle.js")[1]
footer = re.sub("^[^>]*></script>", "", footer)
footer = footer.split("text/javascript")[0]
footer = re.sub("<script [^>]*$", "", footer)
footer = footer.strip() + "\n"
open(domain + "/footer_injection.html", "w").write(footer)

######################################################################
# site.css
######################################################################
print("Processing: site.css")
# Curl the site.css
site_css_url = re.search(r"https://[^\"]+site.css", html)
site_css_url_coords = site_css_url.span()
site_css_url = html[site_css_url_coords[0]:site_css_url_coords[1]]
curl_process = subprocess.run(["curl", site_css_url], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
css_contents = curl_process.stdout

# Parse site.css for our CSS configs
css_contents = css_contents.split("/*! Squarespace LESS Compiler")[-1]
css_contents = re.sub("^[^\*]+\*/", "", css_contents)
css_contents = css_contents.strip()

# Format the css file for writing out to a new file
css_contents = css_contents.replace("{", " {\n")
css_contents = css_contents.replace("}", "\n}\n")
css_contents = css_contents.replace(";", ";\n")
css_contents = css_contents.replace(",", ", ")

css_lines = css_contents.split("\n")
css = ""
cur_indent = 0
for line in css_lines:
    # Dedent for close curly braces
    if "}" in line:
        cur_indent -= 2

    # Process the line
    line = re.sub(r"^ *$", "", line)
    if not line.endswith(";") and (not line.endswith("{")) and (not line.endswith("}")) and (line != ""):
        line = line + ";"
    line = re.sub(r"^( *[^ ]*):", "\g<1>: ", line)
    css += (cur_indent * " ") + line + "\n"
    
    # Indent for close curly braces
    if "{" in line:
        cur_indent += 2

# Write out the site.css
open(domain + "/site.css", "w").write(css)
