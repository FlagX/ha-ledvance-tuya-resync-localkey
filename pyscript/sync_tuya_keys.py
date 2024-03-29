import sys
if "/config/pyscript_modules" not in sys.path:
    sys.path.append("/config/pyscript_modules")

from tuya.api import TuyaAPI
from tuya.exceptions import InvalidAuthentication


@service
def syncTuyaKeys():
    # set `localtuya_title` to your LocalTuya integration title
    localtuya_title = 'localtuya'
    api = TuyaAPI("[REPLACE_WITH_USERNAME]", "[REPLACE_WITH_PASSWORD]")
    await hass.async_add_executor_job(api.login)
    groups = await hass.async_add_executor_job(api.groups);

    localKeys = {};
    for group in groups:
        devs = await hass.async_add_executor_job(api.devices, group['groupId']);
        for dev in devs:
            localKeys[dev.id] = dev.localKey;

    ## update config
    entries = {entry: entry.title for entry in hass.config_entries.async_entries()}
    entry = [key for key, value in entries.items() if value == localtuya_title]
    if entry:
        entry = entry[0]
        for devId in entry.data['devices'].keys():
            localKey = entry.data['devices'][devId]['local_key']
            if (devId in localKeys and localKeys[devId] != localKey):
                log.info('[New] \tdevId: ' + devId + ', localkey: ' + localKey + ' -> ' + localKeys[devId])
                new = {**entry.data}
                new['devices'][devId]['local_key'] = localKeys[devId]
                hass.config_entries.async_update_entry(entry, data=new)
            else:
                log.info('[Unchanged]\t devId: ' + devId + ', localkey: ' + localKey)
    else:
        log.info(f"{localtuya_title} title not found in config. Check the title of your localtuya integration.")
