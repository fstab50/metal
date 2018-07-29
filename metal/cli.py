"""
Summary:
    metal (python3) | Security App Installation & Configuration

Author:
    Blake Huber
    Copyright Blake Huber, All Rights Reserved.

License:
    GNU General Public License v3.0 (GPL-3)
    Additional terms may be found in the complete license agreement:
    https://github.com/fstab50/metal/LICENSE

OS Support:
    - RedHat Linux, Amazon Linux, Ubuntu & variants

Dependencies:
    - Installer tested under py3.5 and py3.6, requires bash v4+ locally
"""

import os
import sys
import platform
import argparse
import inspect
import subprocess
import boto3
from botocore.exceptions import ClientError, ProfileNotFound
from pyaws.core.script_utils import stdout_message, debug_mode
from metal.colors import Colors
from metal import about, logd, __version__
from metal.statics import local_config

try:
    from metal.oscodes_unix import exit_codes
    splitchar = '/'     # character for splitting paths (linux)
except Exception:
    from metal.oscodes_win import exit_codes    # non-specific os-safe codes
    splitchar = '\\'    # character for splitting paths (window

# global objects
logger = logd.getLogger(__version__)
VALID_INSTALL = ('chkrootkit', 'rkhunter')


def authenticated(profile):
    """
    Summary:
        Tests generic authentication status to AWS Account
    Args:
        :profile (str): iam user name from local awscli configuration
    Returns:
        TYPE: bool, True (Authenticated)| False (Unauthenticated)
    """
    try:
        sts_client = boto3_session(service='sts', profile=profile)
        httpstatus = sts_client.get_caller_identity()['ResponseMetadata']['HTTPStatusCode']
        if httpstatus == 200:
            return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            logger.info(
                '%s: Invalid credentials to authenticate for profile user (%s). Exit. [Code: %d]'
                % (inspect.stack()[0][3], profile, exit_codes['EX_NOPERM']['Code']))
        elif e.response['Error']['Code'] == 'ExpiredToken':
            logger.info(
                '%s: Expired temporary credentials detected for profile user (%s) [Code: %d]'
                % (inspect.stack()[0][3], profile, exit_codes['EX_CONFIG']['Code']))
        else:
            logger.exception(
                '%s: Unknown Boto3 problem. Error: %s' %
                (inspect.stack()[0][3], e.response['Error']['Message']))
    except Exception as e:
        return False
    return False


def boto3_session(service, profile=None):
    """
    Summary:
        Establishes boto3 sessions, client
    Args:
        :service (str): boto3 service abbreviation ('ec2', 's3', etc)
        :profile (str): profile_name of an iam user from local awscli config
    Returns:
        TYPE: boto3 client object
    """
    try:
        if profile:
            if profile == 'default':
                client = boto3.client(service)
            else:
                session = boto3.Session(profile_name=profile)
                client = session.client(service)
        else:
            client = boto3.client(service)
    except ClientError as e:
        logger.exception(
            "%s: IAM user or role not found (Code: %s Message: %s)" %
            (inspect.stack()[0][3], e.response['Error']['Code'],
             e.response['Error']['Message']))
        raise
    except ProfileNotFound:
        msg = (
            '%s: The profile (%s) was not found in your local config. Exit.' %
            (inspect.stack()[0][3], profile))
        stdout_message(msg, 'FAIL')
        logger.warning(msg)
        sys.exit(exit_codes['EX_NOUSER']['Code'])
    return client


def help_menu():
    """
    Displays help menu contents
    """
    print(
        Colors.BOLD + '\n\t\t\t  ' + PACKAGE + Colors.RESET +
        ' help contents'
        )
    print(menu_body)
    return


def set_logging(cfg_obj):
    """
    Enable or disable logging per config object parameter
    """
    log_status = cfg_obj['LOGGING']['ENABLE_LOGGING']

    if log_status:
        logger.disabled = False
    elif not log_status:
        logger.info(
            '%s: Logging disabled per local configuration file (%s) parameters.' %
            (inspect.stack()[0][3], cfg_obj['PROJECT']['CONFIG_PATH'])
            )
        logger.disabled = True
    return log_status


def precheck():
    """
    Verify project runtime dependencies
    """
    cfg_path = local_config['PROJECT']['CONFIG_PATH']
    # enable or disable logging based on config/ defaults
    logging = set_logging(local_config)

    if os.path.exists(cfg_path):
        logger.info('%s: config_path parameter: %s' % (inspect.stack()[0][3], cfg_path))
        logger.info(
            '%s: Existing configuration file found. precheck pass.' %
            (inspect.stack()[0][3]))
        return True
    elif not os.path.exists(cfg_path) and logging is False:
        logger.info(
            '%s: No pre-existing configuration file found at %s. Using defaults. Logging disabled.' %
            (inspect.stack()[0][3], cfg_path)
            )
        return True
    if logging:
        logger.info(
            '%s: Logging enabled per config file (%s).' %
            (inspect.stack()[0][3], cfg_path)
            )
        return True
    return False


class SetLogging():
    """
    Summary:
        Initializes project level logging
    Args:
        - **mode (str)**: log_mode, either 'stream' or 'FILE'
        - **disable (bool)**: when True, disables logging output
    Returns:
        TYPE: bool, Success | Failure
    """
    def __init__(self, mode, disable=False):
        self.set(mode, disable)

    def set(self, mode, disable):
        """ create logger object, enable or disable logging """
        global logger
        try:
            if logger:
                if disable:
                    logger.disabled = True
            else:
                if mode in ('STREAM', 'FILE'):
                    logger = logd.getLogger(mode, __version__)
        except Exception as e:
            logger.exception(
                '%s: Problem incurred during logging setup' % inspect.stack()[0][3]
                )
            return False
        return True


def main(operation, profile, auto, debug, user_name=''):
    """
    End-to-end renew of access keys for a specific profile in local awscli config
    """
    if user_name:
        logger.info('user_name parameter given (%s) as surrogate' % user_name)
    try:
        if operation in VALID_INSTALL:
            print(operation)
        elif operation == 'list':
            print(operation)
            return True
        elif not operation:
            msg_accent = (Colors.BOLD + 'list' + Colors.RESET + ' | ' + Colors.BOLD + 'up' + Colors.RESET)
            msg = """You must provide a valid OPERATION for --operation parameter:

                    --operation { """ + msg_accent + """ }
            """
            stdout_message(msg)
            logger.warning('%s: No valid operation provided. Exit' % (inspect.stack()[0][3]))
            sys.exit(exit_codes['E_MISC']['Code'])
        else:
            msg = 'Unknown operation. Exit'
            stdout_message(msg)
            logger.warning('%s: %s' % (msg, inspect.stack()[0][3]))
            sys.exit(exit_codes['E_MISC']['Code'])
    except KeyError as e:
        logger.critical(
            '%s: Cannot find Key %s' %
            (inspect.stack()[0][3], str(e)))
        return False
    except OSError as e:
        logger.critical(
            '%s: problem writing to file %s. Error %s' %
            (inspect.stack()[0][3], output_file, str(e)))
        return False
    except Exception as e:
        logger.critical(
            '%s: Unknown error. Error %s' %
            (inspect.stack()[0][3], str(e)))
        raise e


def options(parser, help_menu=False):
    """
    Summary:
        parse cli parameter options
    Returns:
        TYPE: argparse object, parser argument set
    """
    parser.add_argument("-p", "--profile", nargs='?', default="default",
                              required=False, help="type (default: %(default)s)")
    parser.add_argument("-i", "--install", dest='install', default='NA', type=str, choices=VALID_INSTALL, required=False)
    parser.add_argument("-a", "--auto", dest='auto', action='store_true', required=False)
    parser.add_argument("-c", "--configure", dest='configure', action='store_true', required=False)
    parser.add_argument("-d", "--debug", dest='debug', action='store_true', required=False)
    parser.add_argument("-V", "--version", dest='version', action='store_true', required=False)
    parser.add_argument("-h", "--help", dest='help', action='store_true', required=False)
    return parser.parse_args()


def package_version():
    """
    Prints package version and requisite PACKAGE info
    """
    print(about.about_object)
    sys.exit(exit_codes['EX_OK']['Code'])


def parameters(args):
    parameter_str = ''
    for arg in args:
        parameter_str += arg + ' '
    return parameter_str


def shared_credentials_location():
    """
    Summary:
        Discover alterate location for awscli shared credentials file
    Returns:
        TYPE: str, Full path of shared credentials file, if exists
    """
    if 'AWS_SHARED_CREDENTIALS_FILE' in os.environ:
        return os.environ['AWS_SHARED_CREDENTIALS_FILE']
    return ''


def option_configure(debug=False, path=None):
    """
    Summary:
        Initiate configuration menu to customize metal runtime options.
        Console script ```keyconfig``` invokes this option_configure directly
        in debug mode to display the contents of the local config file (if exists)
    Args:
        :path (str): full path to default local configuration file location
        :debug (bool): debug flag, when True prints out contents of local
         config file
    Returns:
        TYPE (bool):  Configuration Success | Failure
    """
    if CONFIG_SCRIPT in sys.argv[0]:
        debug = True    # set debug mode if invoked from CONFIG_SCRIPT
    if path is None:
        path = local_config['PROJECT']['CONFIG_PATH']
    if debug:
        if os.path.isfile(path):
            debug_mode('local_config file: ', local_config, debug, halt=True)
        else:
            msg = """  Local config file does not yet exist. Run:

            $ metal --configure """
            debug_mode(msg, {'CONFIG_PATH': path}, debug, halt=True)
    r = configuration.init(debug, path)
    return r


def module_path():
    """
    Returns current fs directory location of enclosing module at runtime
    """
    return os.path.dirname(os.path.realpath(__file__))


def rkhunter(caller='console_script'):
    """
    Summary:
        - Console Script target for rkhunter installer
        - Called from either invoking console script "rkinstaller" directly,
          or metal with the --install rkhunter parameter
    Returns:
        Success | Failure, TYPE: bool
    """
    if caller == 'console_script':
        cmd = 'sudo sh rkinstaller.sh ' + parameters(sys.argv[1:])
    else:
        cmd = 'sudo sh rkinstaller.sh ' + parameters(sys.argv[3:])
    try:
        subprocess.call(
                [cmd],
                shell=True,
                cwd=module_path() + '/' + 'rkhunter'
            )
    except Exception as e:
        logger.exception(f'{inspect.stack()[0][3]}: invalid rkhunter installer args. Exit')
        return False
    return True


def init_cli():
    # parser = argparse.ArgumentParser(add_help=False, usage=help_menu())
    parser = argparse.ArgumentParser(add_help=False)

    try:
        args = options(parser)
    except Exception as e:
        help_menu()
        stdout_message(str(e), 'ERROR')
        sys.exit(exit_codes['EX_OK']['Code'])

    if len(sys.argv) == 1:
        help_menu()
        sys.exit(exit_codes['EX_OK']['Code'])

    elif args.help:
        help_menu()
        sys.exit(exit_codes['EX_OK']['Code'])

    elif args.version:
        package_version()

    elif args.configure:
        r = option_configure(args.debug, local_config['PROJECT']['CONFIG_PATH'])
        return r

    elif args.install:
        if args.install == 'rkhunter':
            r = rkhunter(caller='main')
        elif args.install == 'chkrootkit':
            print('invoke chkrootkit installer - FUTURE')
        elif args.install == 'NA':
            print(
                'You must provide either chkrootkit or \
                rkhunter as a parameter when using --install'
                )
        sys.exit(exit_codes['EX_OK']['Code'])

    else:
        if precheck():              # if prereqs set, run
            if authenticated(profile=args.profile):
                # execute keyset operation
                success = main(
                            operation=args.operation,
                            profile=args.profile,
                            user_name=args.username,
                            auto=args.auto,
                            debug=args.debug
                            )
                if success:
                    logger.info('IAM access keyset operation complete')
                    sys.exit(exit_codes['EX_OK']['Code'])
            else:
                stdout_message(
                    'Authenication Failed to AWS Account for user %s' % args.profile,
                    prefix='AUTH',
                    severity='WARNING'
                    )
                sys.exit(exit_codes['E_AUTHFAIL']['Code'])

    failure = """ : Check of runtime parameters failed for unknown reason.
    Please ensure local awscli is configured. Then run keyconfig to
    configure metal runtime parameters.   Exiting. Code: """
    logger.warning(failure + 'Exit. Code: %s' % sys.exit(exit_codes['E_MISC']['Code']))
    print(failure)


if __name__ == '__main__':
    init_cli()
