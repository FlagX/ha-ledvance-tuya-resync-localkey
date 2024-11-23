#!/usr/bin/env python3

import getpass
import os
from typing import Tuple

from pyscript_modules.tuya.api import TuyaAPI
from pyscript_modules.tuya.exceptions import InvalidAuthentication

def get_login() -> Tuple[str, str]:
    def ask_until_ok(fn) -> str:
        while True:
            try:
                return fn()
            except KeyboardInterrupt as e:
                print("Aborted.")
                raise
            except:
                pass
            print()
    return (
        os.getenv("LEDVANCE_USERNAME") or ask_until_ok(lambda: input("Please put your Tuya/Ledvance username: ")),
        os.getenv("LEDVANCE_PASSWORD") or ask_until_ok(lambda: getpass.getpass("Please put your Tuya/Ledvance password: "))
    )

def main():
    username, password = get_login()

    api = TuyaAPI(username, password)
    try:
        api.login()
    except InvalidAuthentication:
        print("Invalid authentication.")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")

    print('---------------------------')
    for group in api.groups():
        for dev in api.devices(group['groupId']):
            print(f'device name:\t{dev.name}')
            print(f'device id:\t{dev.id}')
            print(f'local key:\t{dev.localKey}')
            print('---------------------------')
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()
