# ha-ledvance-tuya-resync-localkey
pyscript for homeassistant to resync local keys from private tuya API.

This also works for Sylvania devices by changing/uncommenting the keys in `pyscript_modules/tuya/const.py`.

This repository includes
  - A script `print-local-keys.py` to print out local keys for your Ledvance devices (They must be already registered in the Ledvance app), which can be used in the [LocalTuya integration](https://github.com/rospogrigio/localtuya) for [Home Assistant](https://www.home-assistant.io/) 
  - Setup via [Pyscript Integration](https://hacs-pyscript.readthedocs.io/en/latest/) to automatically resync local keys

## To just print out your local keys...

First, create a Python 3 environment - version 3.10 is confirmed as working.

Then install the dependencies and run the script:
```
pip install -r requirements.txt
python print-local-keys.py
```
## How to resync local keys automatically (via service)

If you have many devices and reset them sometimes by accident, like me, you can create a service for resyncing the local keys. (New local keys are generated if you reset/re-register your devices).  

### Prerequisites

- [Pyscript Integration](https://hacs-pyscript.readthedocs.io/en/latest/)
- Set `allow_all_imports` and `hass_is_global` to true. (Described [here](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html))
- Ledvance account with devices configured

### Setup

- Replace placeholders in `pyscript\sync_tuya_keys.py` with your Ledvance account credentials.
- Copy `pyscript_modules` and `pyscript` to your Home Assistant config directory.
- In your Home Assistant dashboard should now be under `Developer tools` --> `Services` a service called `Pyscript Python scripting: synctuyakeys` that you can call. (You may have to restart before)
- (If you want Log output, you need to [change the log level to INFO](https://hacs-pyscript.readthedocs.io/en/latest/reference.html#logging) or use [jupyter](https://jupyter.org/install))



## Credits

Credits for the python Tuya API client go to: https://github.com/rgsilva/homeassistant-positivo
I also extracted the keys/secrets by following his guide: https://blog.rgsilva.com/reverse-engineering-positivos-smart-home-app/
