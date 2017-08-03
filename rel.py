
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
import datetime

# Main keys used in the ini file
VERSION = 'version'
URL = 'repository_url'
FOLDER = 'local_folder'
ZIP = 'export_zip'
BASE_SHA = 'base_sha'
ZENODO_ID = 'zenodo'
DOI = 'doi'
ZENODO_FILE_ID = 'zenodo_file'
FULLTITLE = 'fulltitle'
MAINTAINERS = 'maintainers'
AUTHORS = 'authors'
# user override keys in the ini file
FORCE_RECLONE = 'force_clone'
FORCE_RESHA = 'force_sha'
FORCE_REZENODO = 'force_zenodo'
FORCE_REBRANCH = 'force_branch'

GLOBAL_INI = 'global.ini' # global mappings

# Private keys (tokens etc)
ZENODO_SECTION = 'zenodo'
PRIVATE_SITE = 'site'
PRIVATE_TOKEN = 'token'
PRIVATE_INI = 'private.ini' # the file itself

#
HEADERS_JSON = {"Content-Type": "application/json"}

def gen_css(vers, clazz, doi):
    return """
/* version added automatically */
div.{2}:hover::before {0}
    content: "{4}";
{3}
div.{2}::before {0}
    content: "Version {1}";
    font-size: 10px;
    font-family: monospace;
    font-weight: bold;
    line-height: 1;
    /* */
    position: fixed;
    right: 0;
    top: 0;
    z-index: 10;
    /* */
    color: white;
    background: rgb(43, 57, 144);
    padding: 3px;
    border: 1px solid white;
{3}""".format('{', vers, clazz, '}', doi)


def guess_person_name(raw):
    raw = raw.split(' ')
    if '.' in raw[0] or '.' in raw[1]:
        raw = [' '.join(raw[:2])] + raw[2:]
        print("merged", raw)
    return raw[0] , ' '.join(raw[1:])

def create_ini_file():
    preferred_repos = ['hg-novice', 'git-novice', 'make-novice', 'matlab-novice-inflammation', 'python-novice-inflammation', 'r-novice-gapminder', 'r-novice-inflammation', 'shell-novice', 'sql-novice-survey', 'lesson-example', 'instructor-training', 'workshop-template']
    preferred_ini = 'auto.ini'

    parser = argparse.ArgumentParser("Create a skeleton ini file (to copy and edit)")
    parser.add_argument('--version', default=None)
    args = parser.parse_args(sys.argv[1:])

    config = configparser.ConfigParser()
    for r in preferred_repos:
        if r.startswith('dc:'):
            url = "git@github.com:datacarpentry/" + r[3:] + ".git"
        else:
            url = "git@github.com:swcarpentry/" + r + ".git"
        config.add_section(r)
        if args.version is not None:
            config[r][VERSION] = args.version
            config[r][ZIP] = 'zips/'+r+'-'+args.version+'.zip'
        config[r][URL] = url
        config[r][FOLDER] =  ',,'+r

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

def cmd(*args, **kwargs):
    kwmore = {}
    if 'cwd' in kwargs: kwmore['cwd'] = kwargs['cwd']

    if 'getoutput' in kwargs:
        res = subprocess.check_output(args, **kwmore)
    else:
        res = subprocess.call(args, **kwmore)
        if res != 0 and 'noerror' not in kwargs:
            out("!!! ", *args, "RETURNED", res)
            exit(1)
    return res

def git(*args, **kwargs):
    cmd = ["git"] + list(args)
    if 'getoutput' in kwargs:
        res = subprocess.check_output(cmd)
    else:
        res = subprocess.call(cmd)
        if res != 0 and 'noerror' not in kwargs:
            out("!!! git", *args, "RETURNED", res)
    return res

def gitfor(c, *args, **kwargs):
    more = ['-C', c[FOLDER]] + list(args)
    return git(*more, **kwargs)

def new_parser_with_ini_file(*args, **kwargs):
    parser = argparse.ArgumentParser(*args, **kwargs)
    parser.add_argument('ini_file')
    return parser

def out(*args):
    print(*(["#### "] + list(args) + [" ####"]))

def clone_missing_repository():
    parser = new_parser_with_ini_file('Clone the repositories that are not already present.')
    parser.add_argument('--depth', default=None)
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
            if args.depth is None:
                git("clone", c[URL], c[FOLDER])
            else:
                git("clone", "--depth", args.depth, c[URL], c[FOLDER])

def fill_missing_basesha_with_latest():
    parser = new_parser_with_ini_file('Adds the base sha in the ini file, for those who are not present.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("SETTING BASE SHA")
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if BASE_SHA not in c or FORCE_RESHA in c:
            sha = gitfor(c, "rev-parse", "origin/gh-pages", getoutput=True)
            c[BASE_SHA] = sha.decode('utf-8').replace('\n', '')
            out("set sha", c[BASE_SHA])
        # save each time
        save_ini_file(cfg, args.ini_file)

def set_release_version():
    parser = new_parser_with_ini_file('Changes the version in the ini file and the zip path, for all.')
    parser.add_argument('version')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("SETTING VERSION", args.version)
    for r in cfg.sections():
        out("***", r)
        cfg[r][VERSION] = args.version
        cfg[r][ZIP] = 'zips/'+r+'-'+args.version+'.zip'
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
        # save each time
        save_ini_file(cfg, args.ini_file)


def update_zenodo_submission():
    parser = new_parser_with_ini_file('Filling Zenodo submissions.')
    parser.add_argument('--already-published', dest='force_replace', action='store_true')
    parser.set_defaults(force_replace=False)
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
            if args.force_replace:
                out("... discard curnrent changes and unlock for edit")
                discard_url = 'https://{}/api/deposit/depositions/{}/actions/discard?access_token={}'.format(zenodo_site, c[ZENODO_ID], zc[PRIVATE_TOKEN])
                edit_url = 'https://{}/api/deposit/depositions/{}/actions/edit?access_token={}'.format(zenodo_site, c[ZENODO_ID], zc[PRIVATE_TOKEN])
                print(requests.post(discard_url))
                print(requests.post(edit_url))
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
            "communities": [{"identifier": "swcarpentry"}], # TODO maybe use c[COMMUNITIES].split... if generalization is required
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
        if AUTHORS not in c:
            authors = get_sorted_authors(c[FOLDER])
            c[AUTHORS] = ';'.join(authors)
            print(AUTHORS+':', c[AUTHORS])
        # save each time
        save_ini_file(cfg, args.ini_file)

def get_sorted_authors(folder):
    authors = []
    with open (folder+"/AUTHORS", "r") as readme:
        for l in readme.readlines():
            l = l.replace('\n', '')
            if len(l.strip()) == 0: continue
            first_name, last_name = guess_person_name(l)
            authors.append(last_name + ', ' + first_name)
    authors = [a.upper()+' @@@ '+a for a in authors]
    authors = sorted(list(set(authors)))
    authors = [re.sub(r'.* @@@ ', '', a) for a in authors]
    return authors

def branch_build_and_patch_lesson():
    parser = new_parser_with_ini_file('Branch the lesson, build it, patch it, etc.')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    releasemode = read_ini_file(GLOBAL_INI)['relmode']
    out("BUILDING LESSON")
    more = []
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        vers = c[VERSION]
        messageprefix = '[DOI: {}] '.format(c[DOI])
        jekyllversion = cmd('jekyll', '--version', getoutput=True)
        jekyllversion = jekyllversion.decode('utf-8').replace('\n', '')
        cssfile = 'assets/css/lesson.css'
        rmode = ''.join([releasemode[n] for n in releasemode.keys() if n in c[URL]])
        if rmode == '':
            rmode = 'BRANCH'
        # make branch
        out("testing for the presence of ", vers)
        if gitfor(c, 'rev-parse', vers, '--', noerror=True) == 0:
            out("version ", vers, 'already exist')
            if FORCE_REBRANCH not in c:
                continue
            out("recreating branch")
            print(c[BASE_SHA])
            if rmode == 'BRANCH':
                gitfor(c, 'checkout', '-B', c[VERSION], c[BASE_SHA])
                more += ['--force']
        else:
            if rmode == 'BRANCH':
                out("creating branch")
                gitfor(c, 'checkout', '-b', c[VERSION], c[BASE_SHA])
            if rmode == 'TAG':
                gitfor(c, 'checkout', c[BASE_SHA])
        # build etc
        out("building jekyll lesson")
        with open(c[FOLDER]+"/_config.yml", "a") as jekyll_config:
            jekyll_config.write("\n")
            jekyll_config.write("github:\n")
            # TODO may need to tune this swc-releases for generalization
            jekyll_config.write("  url: '/swc-releases/{}/{}'\n".format(vers, r))
            jekyll_config.write("\n")
        cmd('make', 'clean', 'site', cwd=c[FOLDER])
        cmd('find', '.', '-maxdepth', '1', '-exec', 'cp', '-rf', '{}', '../', ';', '-exec', 'git', 'add', '../{}', ';', cwd=c[FOLDER]+'/_site')
        gitfor(c, 'commit',
                  '-m', messageprefix+"Rebuilt HTML files for release "+vers,
                  '-m', 'jekyll version: '+jekyllversion)
        out("adding CSS")
        # TODO remove added css so it can be idempotent (not that useful if it remains deep in the build process though)
        gitfor(c, 'add', cssfile)
        csscontent = gen_css(vers, 'navbar-header', messageprefix)
        with open(c[FOLDER]+'/'+cssfile, 'a') as cssappend:
            cssappend.write(csscontent)
        gitfor(c, 'add', cssfile)
        gitfor(c, 'commit', '-m', messageprefix+'Added version ('+vers+') to all pages via CSS')
        out("pushing?")
        if rmode == 'BRANCH':
            gitfor(c, 'push', *more, '--set-upstream', 'origin', vers)
        if rmode == 'TAG':
            gitfor(c, 'tag', vers)
            gitfor(c, 'push', '--follow-tags', *more, 'origin', 'tag', vers)

def make_zenodo_zip():
    parser = new_parser_with_ini_file('Make the zip for Zenodo')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("ZIPPING LESSON")
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        vers = c[VERSION]
        zipname = c[ZIP]

        gitfor(c, 'archive', '-o', '../'+zipname, '--prefix', r+'/', '-1', vers)

def upload_zenodo_zip():
    parser = new_parser_with_ini_file('Adding zip files to Zenodo submissions.')
    parser.add_argument('--force-replace', dest='force_replace', action='store_true')
    parser.set_defaults(force_replace=False)
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("UPLOADING ZIP TO ZENODO")
    zc = read_ini_file(PRIVATE_INI)[ZENODO_SECTION]
    zenodo_site = zc.get(PRIVATE_SITE) or 'zenodo.org'
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if ZENODO_ID not in c or not os.path.exists(c[ZIP]):
            out("... skipping")
            continue

        # check there are actually no files on zenodo
        list_url = 'https://{}/api/deposit/depositions/{}/files?access_token={}'.format(zenodo_site, c[ZENODO_ID], zc[PRIVATE_TOKEN])
        req = requests.get(list_url)
        resp = req.json()
        if len(resp) == 1:
            if ZENODO_FILE_ID not in c:
                if args.force_replace:
                    out("... there is a file already on zenodo, removing it (due to --force-replace)")
                    requests.delete(resp[0]['links']['self']+'?access_token='+zc[PRIVATE_TOKEN])
                    # go on with the upload
                else:
                    out("... there is a file already on zenodo, getting it's id")
                    c[ZENODO_FILE_ID] = resp[0]['id']
                    continue
            else:
                if c[ZENODO_FILE_ID] == resp[0]['id']:
                    out("... there is a file already on zenodo, with the same id, keeping it")
                else:
                    out("... there is a file already on zenodo, with a different id, skipping !!!!!!!!!!!")
                    out("    remote: ", resp[0]['id'])
                continue
        if len(resp) > 1:
            out("... there are multiple files already on zenodo, skipping")
            continue

        # do upload the file
        with open(c[ZIP], 'rb') as zipfile:
            data = {'filename': re.sub(r'^.*/', '', c[ZIP])}
            files = {'file': zipfile}

            if ZENODO_FILE_ID in c:
                upd_url = 'https://{}/api/deposit/depositions/{}/files/{}?access_token={}'.format(zenodo_site, c[ZENODO_ID], c[ZENODO_FILE_ID], zc[PRIVATE_TOKEN])
                out("... not replacing existing file")
                # put
                continue

            fsize = os.path.getsize(c[ZIP])
            out("... uploading around {}MB".format(fsize/1000/1000))

            add_url = list_url
            req = requests.post(add_url, data=data, files=files)
            resp = req.json()
            if req.status_code // 100 != 2:
                out("ERROR:", req.status_code, resp)
            c[ZENODO_FILE_ID] = resp['id']
            out(ZENODO_FILE_ID+':', c[ZENODO_FILE_ID])

        # save each time
        save_ini_file(cfg, args.ini_file)
    # and at the end (needed due to the complicated logic and "continue" above)
    save_ini_file(cfg, args.ini_file)

def publish_zenodo_submission():
    parser = new_parser_with_ini_file('PUBLISHING Zenodo submissions (cannot be deleted afterwards).')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    out("PUBLISHING THE ZENODO SUBMISSION")
    zc = read_ini_file(PRIVATE_INI)[ZENODO_SECTION]
    zenodo_site = zc.get(PRIVATE_SITE) or 'zenodo.org'
    for r in cfg.sections():
        out("***", r)
        c = cfg[r]
        if ZENODO_ID not in c:
            out("... skipping")
            continue

        # check there are actually no files on zenodo
        pub_url = 'https://{}/api/deposit/depositions/{}/actions/publish?access_token={}'.format(zenodo_site, c[ZENODO_ID], zc[PRIVATE_TOKEN])
        req = requests.post(pub_url)

def git_for_all():
    cfg = read_ini_file(sys.argv[1])
    for r in cfg.sections():
        c = cfg[r]
        out("***", r, "@", c[FOLDER])
        gitfor(c, *sys.argv[2:])

def concat_into(into, *args):
    with open(into, 'w') as outfile:
        for fname in args:
            with open(fname) as infile:
                outfile.write(infile.read())

def manage_authors():
    parser = new_parser_with_ini_file('Help with managing AUTHORS files (DEPRECATED).')
    parser.add_argument('act', help="gather | explore")
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    if args.act == 'gather':
        concat_into(',,all-mailmap', *[cfg[r][FOLDER]+'/.mailmap' for r in cfg.sections()])

def sort_authors():
    parser = new_parser_with_ini_file('Sort AUTHORS files (by last name).')
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    for r in cfg.sections():
        c = cfg[r]
        out("***", r, "@", c[FOLDER])
        authors = get_sorted_authors(c[FOLDER])
        authors = '\n'.join([' '.join(a.split(', ')[::-1]) for a in authors])
        with open(c[FOLDER]+'/AUTHORS', 'w') as authors_file:
            authors_file.write(authors)
            authors_file.write('\n')
        exit

def datemonth_as_text(vers):
    y, m = vers.split('.')
    return datetime.date(int(y), int(m), 1).strftime("%B %Y")

def bibmonth_as_text(vers):
    y, m = vers.split('.')
    return datetime.date(int(y), int(m), 1).strftime("%b").lower()

def publication_record():
    parser = new_parser_with_ini_file('Generate a publication record file.')
    parser.add_argument('--output', '-o', help="file name to generate", default=",,pub.html")
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    with open(args.output, 'w') as o:
        o.write('<ul>\n')
        for r in cfg.sections():
            c = cfg[r]
            eds = c[MAINTAINERS]
            url = 'https://github.com/swcarpentry/git-novice/tree/'+c[VERSION]
            zen = 'https://zenodo.org/record/'+c[ZENODO_ID]
            out("***", r, "@", c[FOLDER])
            o.write('<li>\n')
            o.write('    {} ({}): "{}" Version {}, {},\n'.format(
                ' and '.join(eds.split(';')),
                'eds' if ';' in eds else 'ed',
                c[FULLTITLE],
                c[VERSION],
                datemonth_as_text(c[VERSION])
            ))
            o.write('    <a href="{0}/">{0}</a>\n'.format(url))
            o.write('    <a href="{}">{}</a>\n'.format(zen, c[DOI]))
            o.write('</li>\n')
        o.write('</ul>\n')

def publication_record_bibtex():
    parser = new_parser_with_ini_file('Generate a publication record file.')
    parser.add_argument('--output', '-o', help="file name to generate", default=",,pub.bib")
    parser.add_argument('--type', '-t', help="bibtex entry type", default="misc")
    args = parser.parse_args(sys.argv[1:])
    cfg = read_ini_file(args.ini_file)
    with open(args.output, 'w') as o:
        for r in cfg.sections():
            c = cfg[r]
            bib_id = '{}_{}_{}'.format(
                c[MAINTAINERS].split(',')[0].split(' ')[0].lower(),
                c[VERSION].split('.')[0],
                c[ZENODO_ID])
            tex_authors = ' and '.join(c[MAINTAINERS].split(';'))
            tex_bookauthors = ' and '.join(c[AUTHORS].split(';'))
            eds = c[MAINTAINERS]
            tex_bookeds = ' and '.join(c[MAINTAINERS].split(';'))
            url = 'https://github.com/swcarpentry/git-novice/tree/'+c[VERSION]
            doi_url = 'https://doi.org/'+c[DOI]
            out("***", r, "@", c[FOLDER])
            if args.type == 'book': # generate @book
                o.write('@book{{{},\n'.format(bib_id))
                o.write('  author = {{{}}},\n'.format(tex_bookauthors))
                o.write('  editor = {{({})}},\n'.format(tex_bookeds))
                o.write('  title = {{{}}},\n'.format(c[FULLTITLE]))
                o.write('  month = {},\n'.format(bibmonth_as_text(c[VERSION])))
                o.write('  year = {},\n'.format(c[VERSION].split('.')[0]))
                o.write('  doi = {{{}}},\n'.format(c[DOI]))
                o.write('  url = {{{}}}\n'.format(doi_url))
                o.write('}\n')
                continue
            o.write('@misc{{{},\n'.format(bib_id))
            o.write('  author = {{{}}},\n'.format(tex_authors))
            o.write('  note = {{({})}},\n'.format('eds.' if ';' in eds else 'ed.'))
            o.write('  title = {{{}}},\n'.format(c[FULLTITLE]))
            o.write('  month = {},\n'.format(bibmonth_as_text(c[VERSION])))
            o.write('  year = {},\n'.format(c[VERSION].split('.')[0]))
            o.write('  doi = {{{}}},\n'.format(c[DOI]))
            o.write('  url = {{{}}}\n'.format(doi_url))
            o.write('}\n')
        o.write('\n')
    print("Generated bibtex into '"+str(args.output)+"'")

####################################################

def TODO():
    print("TODO")

commands_map = collections.OrderedDict()
def addcmdmap(k, v, pos=None):
    ind = str(len([k for k in commands_map.keys() if str.isdigit(k) and int(k)!=999]) + 1)
    commands_map[ind if pos is None else pos] = v
    commands_map[k] = v
addcmdmap('ini', create_ini_file)
#addcmdmap('ini:dc', TODO, '999') # TODO generalization
addcmdmap('clone-missing', clone_missing_repository)
addcmdmap('fill-missing-sha', fill_missing_basesha_with_latest)
addcmdmap('create-missing-zenodo', create_missing_zenodo_submission)
addcmdmap('build-and-patch-lesson-branch', branch_build_and_patch_lesson)
addcmdmap('guess-info-from-repo', guess_informations_from_repository)
addcmdmap('update-all-zenodo', update_zenodo_submission)
addcmdmap('make-zenodo-zip', make_zenodo_zip)
addcmdmap('upload-zenodo-zip', upload_zenodo_zip)
#
addcmdmap('final-publish-zenodo', publish_zenodo_submission, '999')
#
addcmdmap('set-release-version', set_release_version, '999')
addcmdmap('git-for-all', git_for_all, '999')
addcmdmap('----authors--rather--use--authorssh', manage_authors, '999')
addcmdmap('print-publication-record', publication_record, '999')
addcmdmap('print-bibtex', publication_record_bibtex, '999')
addcmdmap('sort-authors', sort_authors, '999')


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
