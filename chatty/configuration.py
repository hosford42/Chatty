from typing import Tuple, Dict, Any, Iterable, List
import configparser
import getpass
import os

from chatty.types import HandleConfig, LoginConfig, IPAddress, Handle, Port, Password


def _get_public_config_value(config: configparser.ConfigParser, label: str, section: str, option: str,
                             defaults: Dict[str, Any], needs_save: bool) -> Tuple[str, bool]:
    if config.has_option(section, option):
        return config.get(section, option), needs_save

    if option in defaults:
        value = defaults[option]
    else:
        value = input('%s %s: ' % (label, option)).strip()
    config.set(section, option, value)
    return value, True


def _get_private_config_value(config: configparser.ConfigParser, label: str, section: str, option: str,
                              defaults: Dict[str, Any], needs_save: bool) -> str:
    if config.has_option(section, option):
        return config.get(section, option)

    if option in defaults:
        value = defaults[option]
    else:
        value = getpass.getpass('%s %s: ' % (label, option)).strip()

    if needs_save:
        answer = (input("Save %s %s to config file? (y/N)" % (label, option)).strip() or 'n').lower()
        save = (answer in ('yes', 'y'))
        print("%s %s %s be saved." % (label, option, 'WILL' if save else 'will NOT'))
        if save:
            config.set(section, option, value)

    return value


def get_config(label: str, path: str, public_options: Iterable[str], private_options: Iterable[str],
               **defaults: Any) -> List[str]:
    path = os.path.abspath(os.path.expanduser(path))

    config = configparser.ConfigParser()
    config.read([path])

    needs_save = not config.has_section(label)
    if needs_save:
        config.add_section(label)

    results = []

    for option in public_options:
        value, needs_save = _get_public_config_value(config, label, label, option, defaults, needs_save)
        results.append(value)

    for option in private_options:
        results.append(_get_private_config_value(config, label, label, option, defaults, needs_save))

    if needs_save:
        with open(path, 'w', encoding='utf-8') as config_file:
            config.write(config_file)

        print("%s config saved to %s." % (label, path))

    return results


def get_handle_config(label: str, path: str, **defaults) -> HandleConfig:
    handle, nickname = get_config(label, path, ['handle', 'nickname'], [], **defaults)

    handle = Handle(handle)

    if nickname:
        nickname = Handle(nickname)
    else:
        nickname = None

    return HandleConfig(label, handle, nickname)


def get_login_config(label: str, path: str, **defaults) -> LoginConfig:
    host, port, user, handle_types, password = \
        get_config(label, path, ['host', 'port', 'user', 'handle types'], ['password'], **defaults)

    if host:
        host = IPAddress(host)
    else:
        host = None

    port = int(port or 0)
    if port:
        port = Port(port)
    else:
        port = None

    if user:
        user = Handle(user)
    else:
        user = None

    if password:
        password = Password(password)
    else:
        password = None

    handles = []  # type: List[HandleConfig]
    for handle_type in handle_types.split(','):
        handle_type = handle_type.strip()
        if not handle_type:
            continue
        if handle_type in defaults:
            handle_defaults = defaults[handle_type]
        else:
            handle_defaults = {}
        handles.append(get_handle_config('%s %s' % (label, handle_type), path, **handle_defaults))

    return LoginConfig(label, host, port, user, password, tuple(handles))
