"""
Summary:
    Chkrootkit Installer
    NOTE:  This script must be run with root priviledges

Args:

Returns:
    Success | Failure, TYPE: bool
"""
import os
import sys
import inspect
import hashlib
import tarfile
import subprocess
import urllib.request
import urllib.error
import distro
from metal.script_utils import stdout_message
from metal.colors import Colors
from metal import logd, __version__


try:

    from metal.oscodes_unix import exit_codes
    splitchar = '/'     # character for splitting paths (linux)

except Exception as e:
    msg = 'Import Error: %s. Exit' % str(e)
    stdout_message(msg, 'WARN')
    sys.exit(exit_codes['E_DEPENDENCY']['Code'])


# global objects
logger = logd.getLogger(__version__)
# global objects
BINARY_URL = 'https://s3.us-east-2.amazonaws.com/awscloud.center/chkrootkit/chkrootkit.tar.gz'
MD5_URL = 'https://s3.us-east-2.amazonaws.com/awscloud.center/chkrootkit/chkrootkit.md5'
ACCENT = Colors.BOLD + Colors.BRIGHTWHITE
RESET = Colors.RESET
TMPDIR = '/tmp'


def compile_binary(source):
    """
    Prepare chkrootkit binary
    $ tar xzvf chkrootkit.tar.gz
    $ cd chkrootkit-0.52
    $ make sense
    sudo mv chkrootkit-0.52 /usr/local/chkrootkit
    sudo ln -s
    """
    cmd = 'make sense'
    slink = '/usr/local/bin/chkrootkit'
    target = '/usr/local/chkrootkit/chkrootkit'
    # Tar Extraction
    t = tarfile.open(source, 'r')
    t.extractall(TMPDIR)
    if isinstance(t.getnames(), list):
        extract_dir = t.getnames()[0].split('/')[0]
        os.chdir(TMPDIR + '/' + extract_dir)
        logger.info('make output: \n%s' % subprocess.getoutput(cmd))
        # move directory in place
        os.rename(TMPDIR + '/' + extract_dir, 'usr/local/chkrootkit')
        # create symlink to binary in directory
        os.symlink(target, slink)
        return True
    return False


def download(objects):
    """
    Retrieve remote file object
    """
    def exists(object):
        if os.path.exists(TMPDIR + '/' + filename):
            return True
        else:
            msg = 'File object %s failed to download to %s. Exit' % (filename, TMPDIR)
            logger.warning(msg)
            stdout_message('%s: %s' % (inspect.stack()[0][3], msg))
            return False
    try:
        for file_path in objects:
            filename = file_path.split('/')[-1]
            r = urllib.request.urlretrieve(file_path, TMPDIR + '/' + filename)
            if not exists(filename):
                return False
    except urllib.error.HTTPError as e:
        logger.exception(
            '%s: Failed to retrive file object: %s. Exception: %s, data: %s' %
            (inspect.stack()[0][3], file_path, str(e), e.read()))
        raise e
    return True


def valid_checksum(file, hash_file):
    """
    Summary:
        Validate file checksum using md5 hash
    Args:
        file: file object to verify integrity
        hash_file:  md5 reference checksum file
    Returns:
        Valid (True) | False, TYPE: bool
    """
    bits = 4096
    # calc md5 hash
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(bits), b""):
            hash_md5.update(chunk)
    # locate hash signature for file, validate
    with open(hash_file) as c:
        for line in c.readlines():
            if line.strip():
                check_list = line.split()
                if file == check_list[1]:
                    if check_list[0] == hash_md5.hexdigest():
                        return True
    return False


def which(program):
    """
    Summary:
        Identifies valid binary on Linux systems
    Returns:
        Binary Path (string), otherwise None
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def os_packages(metadata):
    """ Installs operating system dependent packages """
    family = metadata[0]
    release = metadata[1]
    #
    if 'Amazon' in family and release != '2':
        stdout_message('Identified Amazon Linux 1 os distro')
        commands = [
            'sudo yum -y update', 'sudo yum -y groupinstall "Development tools"'
        ]
        for cmd in commands:
            stdout_message(subprocess.getoutput(cmd))
        return True
    elif 'Amazon' in family and release == '2':
        stdout_message('Identified Amazon Linux 2 os distro')
        commands = [
            'sudo yum -y update', 'sudo yum -y groupinstall "Development Tools"'
        ]
        for cmd in commands:
            stdout_message(subprocess.getoutput(cmd))
        return True
    elif 'Redhat' in family:
        stdout_message('Identified Redhat Enterprise Linux os distro')
        commands = [
            'sudo yum -y update', 'sudo yum -y groupinstall "Development tools"'
        ]
        for cmd in commands:
            stdout_message(subprocess.getoutput(cmd))
    elif 'Ubuntu' or 'Mint' in family:
        stdout_message('Identified Ubuntu Linux os distro')
        commands = [
            'sudo apt -y update', 'sudo apt -y upgrade',
            'sudo yum -y groupinstall "Development tools"'
        ]
        for cmd in commands:
            stdout_message(subprocess.getoutput(cmd))
        return True
    return False


def precheck():
    """
    Pre-run dependency check
    """
    binaries = ['make']
    for bin in binaries:
        if not which(bin):
            msg = 'Dependency fail -- Unable to locate rquired binary: '
            stdout_message('%s: %s' % (msg, ACCENT + bin + RESET))
            return False
        elif not root():
            return False
    return True


def main():
    """
    Check Dependencies, download files, integrity check
    """
    # vars
    tar_file = TMPDIR + '/' + BINARY_URL.split('/')[-1]
    chksum = TMPDIR + '/' + MD5_URL.split('/')[-1]
    # url including file path
    urls = (BINARY_URL, MD5_URL)
    # pre-run validation + execution
    if precheck() and os_packages(distro.linux_distribution()):
        stdout_message('begin download')
        if download(urls):
            stdout_message('begin valid_checksum')
            valid_checksum(tar_file, chksum)
            return compile_binary(tar_file)
    logger.warning('%s: Pre-run dependency check fail - Exit' % inspect.stack()[0][3])
    return False


def root():
    """
    Checks localhost root or sudo access
    """
    if os.geteuid() == 0:
        return True
    elif subprocess.getoutput('sudo echo $EUID') == '0':
        return True
    return False


if __name__ == '__main__':
    sys.exit(main())
