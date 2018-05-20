import configparser
import getpass
import os

from chatty.types import ProtocolConfig, IPAddress, Handle, Port, Password


def get_protocol_config(protocol: str, default_port: int, path: str) -> ProtocolConfig:
    path = os.path.abspath(os.path.expanduser(path))

    protocol = protocol.upper()

    config = configparser.ConfigParser()
    config.read([path])

    needs_save = not config.has_section(protocol)
    if needs_save:
        config.add_section(protocol)

    host = config.get(protocol, 'host', fallback='localhost')
    port = config.getint(protocol, 'port', fallback=default_port)
    user = config.get(protocol, 'user', fallback=getpass.getuser())

    if config.has_option(protocol, 'handle'):
        handle = config.get(protocol, 'handle')
    else:
        handle = input("%s address, identifier, or handle: " % protocol).strip()
        needs_save = True

    nickname = config.get(protocol, 'nickname', fallback=None) or None

    if config.has_option(protocol, 'password'):
        password = config.get(protocol, 'password')
    else:
        password = getpass.getpass("%s test acct password: " % protocol)
        if needs_save:
            answer = (input("Save %s password to test config file? (y/N)" % protocol).strip() or 'n').lower()
            save_password = (answer in ('yes', 'y'))
            print("%s password %s be saved." % (protocol, 'WILL' if save_password else 'will NOT'))
            if save_password:
                config.set(protocol, 'password', password)

    if needs_save:
        config.set(protocol, 'host', host)
        config.set(protocol, 'port', str(port))
        config.set(protocol, 'user', user)
        config.set(protocol, 'handle', handle)
        config.set(protocol, 'nickname', nickname or '')

        with open(path, 'w', encoding='utf-8') as config_file:
            config.write(config_file)

        print("%s config saved to %s." % (protocol, path))

    return ProtocolConfig(
        IPAddress(host),
        Port(port),
        Handle(user),
        Password(password),
        Handle(handle),
        Handle(nickname) if nickname else None
    )
