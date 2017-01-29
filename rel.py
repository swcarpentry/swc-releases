
import argparse
import configparser
import sys
import os
import subprocess
import shutil
import collections
import json
import requests
import yaml
import re


# Main keys used in the ini file
URL = 'repository_url'
FOLDER = 'local_folder'
BASE_SHA = 'base_sha'
ZENODO_ID = 'zenodo'
DOI = 'doi'
FULLTITLE = 'fulltitle'
MAINTAINERS = 'maintainers'
AUTHORS = 'authors'
# user override keys in the ini file
FORCE_RECLONE = 'force_clone'
FORCE_RESHA = 'force_sha'
FORCE_REZENODO = 'force_zenodo'

GLOBAL_INI = 'global.ini' # global mappings

# Private keys (tokens etc)
ZENODO_SECTION = 'zenodo'
PRIVATE_SITE = 'site'
PRIVATE_TOKEN = 'token'
PRIVATE_INI = 'private.ini' # the file itself

#
HEADERS_JSON = {"Content-Type": "application/json"}

def guess_person_name(raw):
    raw = raw.split(' ')
    if '.' in raw[0] or '.' in raw[1]:
        raw = [' '.join(raw[:2])] + raw[2:]
        print("merged", raw)
    return raw[0] , ' '.join(raw[1:])

def create_ini_file():
    preferred_repos = ['hg-novice', 'git-novice', 'make-novice', 'matlab-novice-inflammation', 'python-novice-inflammation', 'r-novice-gapminder', 'r-novice-inflammation', 'shell-novice', 'sql-novice-survey', 'lesson-example', 'instructor-training', 'workshop-template']
    preferred_ini = 'auto.ini'

    config = configparser.ConfigParser()
    for r in preferred_repos:
        if r.startswith('dc:'):
            url = "git@github.com:datacarpentry/" + r[3:] + ".git"
        else:
            url = "git@github.com:swcarpentry/" + r + ".git"
        config[r] = {
        URL: url,
        FOLDER: ',,'+r,
        }

    save_ini_file(config, preferred_ini)

    print("Default ini file has been generated in <<", preferred_ini, ">>.")
    print("Copy and possibly modify this file.")
    print("You'll need to pass it's name to most other commands.")

def save_ini_file(cfg, ini_file):
    with open(ini_file, 'w') as configfile:
        cfg.write(configfile)

def read_ini_file(ini_file):
    cfg = configparser.ConfigParser()
    cfg.read(ini_file)
    return cfg

def git(*args, **kwargs):
    cmd = ["git"] + list(args)
    if 'getoutput' in kwargs:
        res = subprocess.check_output(cmd)
    else:
        res = subprocess.call()
        if res != 0:
            out("!!! git", *args, "RETURNED", res)
    return res

def gitfor(c, *args, **kwargs):
    cmd = ["git", "-C", c[FOLDER]] + list(args)
    if 'getoutput' in kwargs:
        res = subprocess.check_output(cmd)
    else:
        res = subprocess.call(cmd)
        if res != 0:
            out("!!! git -C", c[FOLDER], *args, "RETURNED", res)
    return res

def new_parser_with_ini_file(*args, **kwargs):
    parser = argparse.ArgumentParser(*args, **kwargs)
    parser.add_argument('ini_file')
    return parser

def out(*args):
    print(*(["#### "] + list(args) + [" ####"]))

def clone_missing_repositories():
    parser = new_parser_with_ini_file('Clone the repositories that are not already present.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("CLONING")
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if os.path.isdir(c[FOLDER]):
            if FORCE_RECLONE in c:
                out("removing (forced)", c[FOLDER])
                shutil.rmtree(c[FOLDER])
        if os.path.isdir(c[FOLDER]):
            out("skipped...")
        else:
            git("clone", c[URL], c[FOLDER])

def fill_missing_basesha_with_latest():
    parser = new_parser_with_ini_file('Adds the base sha in the ini file, for those who are not present.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("SETTING BASE SHA")
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if BASE_SHA not in c or FORCE_RESHA in c:
            sha = gitfor(c, "rev-parse", "gh-pages", getoutput=True)
            c[BASE_SHA] = sha.decode('utf-8').replace('\n', '')
            out("set sha", c[BASE_SHA])
    save_ini_file(cfg, args.ini_file)

def create_missing_zenodo_submission():
    parser = new_parser_with_ini_file('Creating Zenodo submission for those who have none.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("CREATING ZENODO ENTRY")
    zc = read_ini_file(PRIVATE_INI)[ZENODO_SECTION]
    zenodo_site = zc.get(PRIVATE_SITE) or 'zenodo.org'
    create_url = 'https://{}/api/deposit/depositions/?access_token={}'.format(zenodo_site, zc[PRIVATE_TOKEN])
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if ZENODO_ID not in c or FORCE_REZENODO in c:
            req = requests.post(create_url, data="{}", headers=HEADERS_JSON)
            json = req.json()
            c[ZENODO_ID] = str(json['id'])
            c[DOI] = json['metadata']['prereserve_doi']['doi']
            out("got new zenodo id", c[ZENODO_ID])
    save_ini_file(cfg, args.ini_file)


def update_zenodo_submission():
    parser = new_parser_with_ini_file('Filling Zenodo submissions.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("UPDATING ZENODO ENTRY")
    zc = read_ini_file(PRIVATE_INI)[ZENODO_SECTION]
    zenodo_site = zc.get(PRIVATE_SITE) or 'zenodo.org'
    dc = read_ini_file(GLOBAL_INI)['description']
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if ZENODO_ID in c:
            update_url = 'https://{}/api/deposit/depositions/{}?access_token={}'.format(zenodo_site, c[ZENODO_ID], zc[PRIVATE_TOKEN])
            description = ''.join([dc[n] for n in dc.keys() if n in c[URL]])
            if len(description) == 0:
                description = "TODO DESCRIPTION"
                out("!!! missing description")
            metadata = {"metadata": {
            "title": c[FULLTITLE],
            "upload_type": "lesson",
            "description": description,
            "contributors": [{"name": m, "type": "Editor"} for m in c[MAINTAINERS].split(';')],
            "creators": [{"name": m} for m in c[AUTHORS].split(';')],
            "communities": [{"identifier": "swcarpentry"}], # TODO maybe use c[COMMUNITIES].split... if generalisation is required
            }}
            req = requests.put(update_url, data=json.dumps(metadata), headers=HEADERS_JSON)
            resp = req.json()
            if req.status_code // 100 != 2:
                out("ERROR:", req.status_code, resp)
            assert c[DOI] == resp['metadata']['prereserve_doi']['doi']
            assert len(resp['metadata']['communities']) > 0


def guess_informations_from_repository():
    parser = new_parser_with_ini_file('Creating Zenodo submission for those who have none.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("EXTRACTING LESSON INFO")
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        with open(c[FOLDER]+"/_config.yml", "r") as jekyll_config:
            yml = yaml.load(jekyll_config)
        # title
        title = yml['title']
        if r == 'lesson-example': title = "Example Lesson"
        if r == 'workshop-template': title = "Workshop Template"
        if yml['carpentry'] == 'swc': title = "Software Carpentry: "+title
        if yml['carpentry'] == 'dc':  title = "Data Carpentry: "+title
        if FULLTITLE not in c:
            c[FULLTITLE] = title
            print(FULLTITLE+':', c[FULLTITLE])
        # maintainers from the readme
        maintainers = []
        if MAINTAINERS not in c:
            with open (c[FOLDER]+"/README.md", "r") as readme:
                mode = 0
                for l in readme.readlines():
                    l = l.replace('\n', '')
                    if mode==1 and len(l.strip()) > 0: mode = 2
                    if mode==2 and len(l.strip()) == 0: break
                    if mode==2:
                        if '[' not in l: continue
                        raw = re.sub(r'''^[^[]*\[([^]]*)\].*$''', r'\1', l)
                        if '[' in raw: continue # replace failed?
                        first_name, last_name = guess_person_name(raw)
                        maintainers.append(last_name + ', ' + first_name)
                    if mode==0 and 'aintainer' in l: mode = 1
            c[MAINTAINERS] = ';'.join(maintainers)
            print(MAINTAINERS+':', c[MAINTAINERS])
        # authors from the AUTHORS file
        # cat ,,*/AUTHORS |sort |uniq|grep -v '^[^ ]* [^ ]*$'
        authors = []
        if AUTHORS not in c:
            with open (c[FOLDER]+"/AUTHORS", "r") as readme:
                for l in readme.readlines():
                    l = l.replace('\n', '')
                    if len(l.strip()) == 0: continue
                    first_name, last_name = guess_person_name(l)
                    authors.append(last_name + ', ' + first_name)
            c[AUTHORS] = ';'.join(authors)
            print(AUTHORS+':', c[AUTHORS])
    save_ini_file(cfg, args.ini_file)

####################################################

def TODO():
    print("TODO")

commands_map = collections.OrderedDict()
def addcmdmap(k, v, pos=None): commands_map[str(len(commands_map)//2 + 1) if pos is None else pos] = v ; commands_map[k] = v
addcmdmap('ini', create_ini_file)
#addcmdmap('ini:dc', TODO, '999')
addcmdmap('clone-missing', clone_missing_repositories)
addcmdmap('fill-missing-sha', fill_missing_basesha_with_latest)
addcmdmap('create-missing-zenodo', create_missing_zenodo_submission)
addcmdmap('guess-info-from-repo', guess_informations_from_repository)
addcmdmap('update-all-zenodo', update_zenodo_submission)
addcmdmap('build-and-patch-lesson', TODO)
#...
addcmdmap('make-zenodo-zip', TODO)
addcmdmap('upload-zenodo-zip', TODO)

def usage(info):
    print("USAGE",'('+str(info)+')')
    print("Available commands:")
    for c in commands_map.keys():
        if str.isdigit(c):
            if int(c)!=999:
                print(c, ') ', sep='', end='')
        else: print(c)

def main():
    if len(sys.argv) <= 1:
        usage(1)
    else:
        command = sys.argv[1]
        sys.argv = [' '.join(sys.argv[:2])] + sys.argv[2:]
        if command in commands_map.keys():
            commands_map[command]()
        else:
            usage(2)

if __name__ == '__main__':
    main()
