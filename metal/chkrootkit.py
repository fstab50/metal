"""
Summary:
    Chkrootkit Installer
Args:

Returns:
    Success | Failure, TYPE: bool


    wget ftp://ftp.pangeia.com.br/pub/seg/pac/chkrootkit.tar.gz
    $ tar xzvf chkrootkit.tar.gz
    wget ftp://ftp.pangeia.com.br/pub/seg/pac/chkrootkit.md5
    $ md5sum -c chkrootkit.md5
    $ cd chkrootkit-0.52
    $ make sense
    sudo mv chkrootkit-0.52 /usr/local/chkrootkit
    sudo ln -s /usr/local/chkrootkit/chkrootkit  /usr/local/bin/chkrootkit

"""
import os
import sys
import inspect
import hashlib
import urllib.request
from urllib import parse
import urllib.error
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
BINARY_URL = 'ftp://ftp.pangeia.com.br/pub/seg/pac/chkrootkit.tar.gz'
MD5_URL = 'ftp://ftp.pangeia.com.br/pub/seg/pac/chkrootkit.md5'
ACCENT = Colors.BOLD + Colors.BRIGHTWHITE
RESET = Colors.RESET
TMPDIR = '/tmp'


def download(filename):
    """ Retrieve remote file object """
    urls = (BINARY_URL, MD5_URL)
    try:
        for file_path in urls:
            filename = file_path.split('/')[-1]
            r = urllib.request.urlretrieve(url, TMPDIR + '/' + filename)
            if not os.path.exists(TMPDIR + '/' + filename):
                msg = 'File object %s failed to download to %s. Exit' % (filename, TMPDIR)
                logger.warning(msg)
                stdout_message('%s: %s' % (inspect.stack()[0][3], msg))
                return False
    except urllib.error.HTTPError as e:
        logger.exception(
            '%s: Failed to retrive file object: %s. Exception: %s, data: %s' %
            (inspect.stack()[0][3], url, str(e), e.read())
        raise e


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


def precheck():
    """ pre-run dependency check """
    if not which('make'):
        msg = 'dependency fail -- Unable to locate rquired binary: '
        stdout_message('%s: %s' % (msg, ACCENT + 'make' + RESET))
        return False
    return True


def main():
    """ Initializes script """
    if precheck():

    else:
        sys.exit(exit_codes['E_DEPENDENCY']['Code'])


if __main__ == '__name__':
    sys.exit(main())
