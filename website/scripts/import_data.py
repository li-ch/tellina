import html
import os, sys
import pickle
import re
import sqlite3

from website.models import URL, URLTag
from website.utils import get_tag, get_command, get_url

learning_module_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                                   "tellina_learning_module")
sys.path.append(learning_module_dir)

from bashlex import data_tools


CODE_REGEX = re.compile(r"<pre><code>([^<]+\n[^<]*)<\/code><\/pre>")

def extract_code(text):
    for match in CODE_REGEX.findall(text):
        if match.strip():
            yield html.unescape(match.replace("<br>", "\n"))

def extract_oneliner_from_code(code_block):
    cmd = code_block.splitlines()[0]
    if cmd.startswith('$ '):
        cmd = cmd[2:]
    if cmd.startswith('# '):
        cmd = cmd[2:]

    cmd = cmd.strip()

    # discard code block opening line
    if cmd.endswith('{') or cmd.endswith('[') or cmd.endswith('('):
        return None

    return cmd 

def load_urls(input_file_path):
    with open(input_file_path, 'rb') as f:
        urls_by_utility = pickle.load(f)

    for utility in urls_by_utility:
        for url in urls_by_utility[utility]:
            if not URLTag.objects.filter(url__str=url, tag=utility):
                URLTag.objects.create(url__str=url, tag=utility)
                print("Add {}, {}".format(url, utility))


def load_commands_in_url(stackoverflow_dump_path):
    url_prefix = 'https://stackoverflow.com/questions/'

    with sqlite3.connect(stackoverflow_dump_path, detect_types=sqlite3.PARSE_DECLTYPES) as db:
        for url in URL.objects.all():
            print(url.str)
            for answer_body, in db.cursor().execute("""
                    SELECT answers.Body FROM answers 
                    WHERE answers.ParentId = ?""", (url.str[len(url_prefix):], )):
                url.html_content = answer_body
                url.save()

                url.commands.clear()
                for code_block in extract_code(url.html_content):
                    cmd = extract_oneliner_from_code(code_block)
                    if cmd:
                        print(cmd)
                        command = get_command(cmd)
                        url.commands.add(command)
                        url.save()


if __name__ == '__main__':
    load_urls()
