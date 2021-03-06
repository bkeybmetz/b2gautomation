from mozprocess import ProcessHandler
from optparse import OptionParser
import os
import shutil
import tempfile
from xml.dom.minidom import parse


def execute_cmd(cmd, cwd):
    print 'executing', cmd
    proc = ProcessHandler(cmd, cwd=cwd)
    assert(proc.waitForFinish(timeout=180) == 0)

def update_manifest(src_dom, src_manifest, dest_manifest):
    dest_dom = parse(src_manifest)
    src_projects = src_dom.getElementsByTagName('project')
    dest_projects = dest_dom.getElementsByTagName('project')

    for dest_project in dest_projects:
        dest_path = dest_project.getAttribute('path')
        dest_name = dest_project.getAttribute('name')
        for src_project in src_projects:
            src_path = src_project.getAttribute('path')
            src_name = src_project.getAttribute('name')
            src_revision = src_project.getAttribute('revision')
            if (dest_path == src_path and dest_name == src_name
                                      and src_revision
                                      and dest_project.hasAttribute('revision')):
                dest_project.setAttribute('revision', src_revision)

    f = open(dest_manifest, 'w')
    dest_dom.writexml(f)

def make_device_manifests(template_manifest):
    dom = parse(template_manifest)
    cwd = os.getcwd()
    git_dir = os.path.join(cwd, 'manifest_repo')
    if os.access(git_dir, os.F_OK):
        shutil.rmtree(git_dir)

    # clone the manifest repo
    cmd = ['git', 'clone', 'git://github.com/mozilla-b2g/b2g-manifest.git', 'manifest_repo']
    execute_cmd(cmd, cwd)

    # switch to the galaxy-s2 branch
    cmd = ['git', 'checkout', 'galaxy-s2']
    execute_cmd(cmd, git_dir)

    # generate the galaxy-s2 manifest
    update_manifest(dom,
                    os.path.join(git_dir, 'default.xml'),
                    os.path.join(os.path.dirname(template_manifest), 'default-sgs2.xml'))

    # switch to the crespo (nexus-s) branch
    cmd = ['git', 'checkout', 'crespo']
    execute_cmd(cmd, git_dir)

    # generate the nexus-s manifest
    update_manifest(dom,
                    os.path.join(git_dir, 'default.xml'),
                    os.path.join(os.path.dirname(template_manifest), 'default-nexuss.xml'))

    # remove the git directory
    shutil.rmtree(git_dir)

if __name__ == '__main__':
    parser = OptionParser(usage='%prog [options] /path/to/template/manifest')
    options, args = parser.parse_args()
    if not args:
        parser.print_usage()
        parser.exit()

    make_device_manifests(args[0])

