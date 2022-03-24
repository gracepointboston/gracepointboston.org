#!/usr/bin/env python3

import os
import re
import subprocess
import sys

def curl(url):
    curl_process = subprocess.run(["curl", url], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    html = curl_process.stdout
    return html

def parse_html_for_code_blocks(html, process_footer=False):
    cur_section_name = None
    if process_footer:
        html = "<footer " + html.split("<footer ")[1]
        cur_section_name = "footer"
    else:
        html = html.split("<footer ")[0]

    code_blocks = {}
    in_code_block = False
    code_block = ""
    num_open_tags = 0
    for line in html.split("\n"):
        line_processed = False
        while not line_processed:
            line_processed = True
            if not in_code_block:
                if "sqs-block-code" in line: # Don't regex check if unnecessary for performance reasons
                    regex = r"<div .*class=\".*sqs-block-code.*\"[^>]*>"
                    search = re.search(regex, line)
                    if search:
                        in_code_block = True
                        num_open_tags = 1
                        match_end = search.span()[-1]
                        line = line[match_end:]
                        line_processed = False
                if "<section " in line:
                    search_type = "id"
                    regex = r"<section.* id=\"[^\"]*\""
                    search = re.search(regex, line)
                    if search == None:
                        search = re.search(r"<section.* class=\"[^\"]*\"", line)
                        search_type = "class"
                    section_name_search_coords = search.span()
                    section_name_match = line[section_name_search_coords[0]:section_name_search_coords[1]]
                    section_name = section_name_match.split(" " + search_type + "=\"")[1].split("\"")[0]
                    cur_section_name = section_name.strip()
            else:
                in_tag = False
                in_double_quotes = False
                in_single_quotes = False
                for char_idx in range(len(line)):
                    c = line[char_idx]
                    if (not in_single_quotes) and (c == "\""):
                        in_double_quotes = not in_double_quotes
                    elif (not in_double_quotes) and (c == "'"):
                        in_single_quotes = not in_single_quotes
                    elif (not in_single_quotes) and (not in_double_quotes) and (c == "<"):
                        if line[char_idx + 1] == "/": # Close tag
                            num_open_tags -= 1
                        else: # If not close, then it's open... unless the last char of the tag is "/" - we'll check for this when we come across the ">" char at the end of the tag
                            num_open_tags += 1
                    elif (not in_single_quotes) and (not in_double_quotes) and (c == ">"):
                        if line[char_idx - 1] == "/": # This was an open and close tag like <br/>
                            num_open_tags -= 1

                    if (num_open_tags > 0):
                        code_block += c
                    else:
                        code_block += line[0:char_idx]
                        if cur_section_name not in code_blocks:
                            code_blocks[cur_section_name] = []
                        code_blocks[cur_section_name].append(code_block.strip() + "\n")
                        code_block = ""
                        in_code_block = False
                        line = line[(char_idx + 1):]
                        line_processed = False
                        break
                code_block += "\n"
    return code_blocks

def get_page_url(url):
    page_url = url.split(".org")[1]
    if page_url == "":
        page_url = "home"
    else:
        page_url = re.sub(r"^/+", "", page_url).strip()
    return page_url

def write_code_blocks(url, all_code_blocks, custom_url=None):
    if len(all_code_blocks.keys()) > 0: # Only create outside folders if there are code blocks to be written out
        orig_dir = os.getcwd()
        domain = "www.gracepointboston.org/"
        site_dir = domain + get_page_url(url)
        if custom_url != None:
            site_dir = domain + custom_url
        os.makedirs(site_dir, exist_ok=True)
        os.chdir(site_dir)

        for section_name, code_blocks in all_code_blocks.items():
            domain_dir = os.getcwd()
            os.makedirs(section_name, exist_ok=True)
            os.chdir(section_name)

            block_index = 1
            for code_block in code_blocks:
                open(section_name + "_" + str(block_index), 'w').write(code_block)
                block_index += 1

            os.chdir(domain_dir)
        os.chdir(orig_dir)

def extract(url):
    print("Processing: " + url)
    html = curl(url)
    all_code_blocks = parse_html_for_code_blocks(html, False)
    write_code_blocks(url, all_code_blocks)
    if (get_page_url(url) == "home"):
        all_code_blocks = parse_html_for_code_blocks(html, True)
        write_code_blocks(url, all_code_blocks, "")

if len(sys.argv) > 1:
    url = sys.argv[1].strip()
    extract(url)
else:
    print("Usage: python extract_code_blocks.py URL_TO_PROCESS")
