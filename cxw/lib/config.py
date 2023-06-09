import toml
import pathlib

# read toml config file
current_dir = pathlib.Path(__file__).parent.parent.absolute()
config = toml.load(current_dir / 'config.toml')

def get_config(key, default=None, strict=True):
    """
    Get config value by key if strict is True, raise KeyError if key not found
    if strict is False, return default value if key not found
    :param key: str like 'a.b.c'
    :param default: default value Default: None
    :param strict: strict mode Default: True
    :return:
    """
    conf = config.copy()
    for k in key.split('.'):
        if isinstance(conf, dict):
            conf = conf.get(k, default)
        else:
            conf = default
    if strict and conf is default:
        raise KeyError(f'Key {key} not found')
    return conf


PROTOCOL = get_config('network.protocol', strict=True)
HOST = get_config('network.host', strict=True)
SIGNATURE_SALT = get_config('network.interceptors.signature_salt', strict=True)
DEVICE_ID = get_config('device.device-id', strict=True)
USER_AGENT = get_config('device.headers.user-agent', strict=True)
CUSTOM_USER_AGENT = get_config('device.headers.custom-user-agent', strict=True)
USER_ID = get_config('user.user-id', strict=True)
ACCOUNT_ID = get_config('user.account-id', strict=True)
SESSION_ID = get_config('user.session-id', strict=True)
LOCATION = get_config('answer.location', strict=True)
# Optional
LARK = get_config('bot.lark', strict=False)
LARK_WEBHOOK = get_config('bot.lark.webhook', strict=False)
LARK_SECRET = get_config('bot.lark.secret', strict=False)

__dict__ = {
    'PROTOCOL': PROTOCOL,
    'HOST': HOST,
    'SIGNATURE_SALT': SIGNATURE_SALT,
    'DEVICE_ID': DEVICE_ID,
    'USER_AGENT': USER_AGENT,
    'CUSTOM_USER_AGENT': CUSTOM_USER_AGENT,
    'USER_ID': USER_ID,
    'ACCOUNT_ID': ACCOUNT_ID,
    'SESSION_ID': SESSION_ID,
    'LOCATION': LOCATION,
    'LARK': LARK,
    'LARK_WEBHOOK': LARK_WEBHOOK,
    'LARK_SECRET': LARK_SECRET,
}

if __name__ == '__main__':
    print(__dict__)
