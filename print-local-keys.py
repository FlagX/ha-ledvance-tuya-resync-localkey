from pyscript_modules.tuya.api import TuyaAPI
from pyscript_modules.tuya.exceptions import InvalidAuthentication

api = TuyaAPI("[REPLACE_WITH_USERNAME]", "[REPLACE_WITH_PASSWORD")
api.login()

for group in api.groups():
    for dev in api.devices(group['groupId']):
        print(f'device name:\t{dev.name}')
        print(f'device id:\t{dev.id}')
        print(f'local key:\t{dev.localKey}')
        print('---------------------------')
