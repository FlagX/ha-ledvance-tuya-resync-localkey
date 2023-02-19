import base64
import logging
import hmac
import hashlib
import json
from Crypto.Util.number import long_to_bytes
import requests
import time
import uuid

from Crypto.PublicKey import RSA

from .textbook_rsa import new as new_textbook_rsa
from .const import *
from .exceptions import *

PRODUCT_TYPES = {
  "pq860vo9ib50jhud": "switch",
  "lwpag3bu0faaowlj": "smart_ir",
  "trp7wywx3yx8yild": "remote", # light
  "ZAx1jolkKaiu8JtM": "remote"  # tv
}

API_VERSION_FOR_ACTION = {
  "tuya.m.infrared.keydata.get": "2.0",
  "tuya.m.device.sub.list": "1.1",
}
DEFAULT_API_VERSION = "1.0"

IR_VENDOR = "3"

logger = logging.getLogger(__name__)

class TuyaDevice:
  def __init__(self, api, dev_info, gateway_id=None):
    self.api = api

    # print(json.dumps(dev_info, indent=2))

    self._schema = json.loads(dev_info["schema"])
    self._id = dev_info["devId"]
    self._gateway_id = dev_info["devId"] if gateway_id is None else gateway_id
    self._dps = dev_info["dps"]
    self._name = dev_info["name"]
    self._online = dev_info["isOnline"]
    self._product = PRODUCT_TYPES[dev_info["productId"]] if dev_info["productId"] in PRODUCT_TYPES else "unknown"
    self._localKey = dev_info["localKey"]

  @property
  def localKey(self):
    return self._localKey


  @property
  def schema(self):
    return self._schema


  @property
  def id(self):
    return self._id


  @property
  def gateway_id(self):
    return self._gateway_id


  @property
  def dps(self):
    return self._dps


  @property
  def name(self):
    return self._name


  @property
  def product(self):
    return self._product


  @property
  def online(self):
    return self._online


  def set_dps(self, dps, value):
    success = self.api.set_dps(self._id, self._gateway_id, {dps: value})
    if success is True:
      self._dps[dps] = value
    return success


  def set_dps_many(self, dps_values):
    success = self.api.set_dps(self._id, self._gateway_id, dps_values)
    if success is True:
      self._dps = {**self._dps, **dps_values}
    return success


  def refresh(self):
    self._online = self.api._device_info(self._id)["isOnline"]
    self._dps = self.api.get_dps(self._id)



class TuyaAPI:
  def __init__(self,
               email: str,
               password: str,
               client_id: str = TUYA_CLIENT_ID,
               tuya_key: str = TUYA_SECRET_KEY,
               country_code: int = TUYA_COUNTRY_CODE):
    self._email = email
    self._password = password
    self._client_id = client_id
    self._tuya_key = tuya_key
    self._country_code = country_code

    self.session = requests.session()
    self.sid = None


  def _api(self, options, post_data=None, requires_sid=True, do_not_relogin=False):
    headers = {"User-Agent": TUYA_USER_AGENT}

    data = {"postData": json.dumps(post_data, separators=(',', ':'))} if post_data is not None else None
    sanitized_options = {**options}
    if "action" in sanitized_options:
      sanitized_options["a"] = options["action"]
      del sanitized_options["action"]
    
    api_version = API_VERSION_FOR_ACTION[options["action"]] if options["action"] in API_VERSION_FOR_ACTION else DEFAULT_API_VERSION

    params = {
      "appVersion": "1.1.6",
      "appRnVersion": "5.14",
      "channel": "oem",
      "deviceId": TUYA_DEVICE_ID,
      "platform": "Linux",
      "requestId": str(uuid.uuid4()),
      "lang": "en",
      "clientId": self._client_id,
      "osSystem": "9",
      "os": "Android",
      "timeZoneId": "America/Sao_Paulo",
      "ttid": "sdk_tuya@" + self._client_id,
      "et": "0.0.1",
      "v": api_version,
      "sdkVersion": "3.10.0",
      "time": str(int(time.time())),
      **sanitized_options
    }

    if requires_sid:
      if self.sid is None:
        raise ValueError("You need to login first.")
      params["sid"] = self.sid

    sanitized_data = data if data is not None else {}
    params["sign"] = self._sign({**params, **sanitized_data})

    result = None
    try:
 
      result = self._handle(self.session.post(TUYA_ENDPOINT, params=params, data=data, headers=headers).json())
      logger.debug("Request: options %s, headers %s, params %s, data %s, result %s", options, headers, params, data, result)
    except InvalidUserSession:
      if not do_not_relogin:
        logger.info("Session is no longer valid, logging in again")
        self.login()
        result = self._api(options, post_data, requires_sid, True)

    return result


  def _sign(self, data):
    KEYS_TO_SIGN = ['a', 'v', 'lat', 'lon', 'lang', 'deviceId', 'imei',
                    'imsi', 'appVersion', 'ttid', 'isH5', 'h5Token', 'os',
                    'clientId', 'postData', 'time', 'requestId', 'n4h5', 'sid',
                    'sp', 'et']

    sorted_keys = sorted(list(data.keys()))

    # Create string to sign
    strToSign = ""
    for key in sorted_keys:
      if key not in KEYS_TO_SIGN or key not in data or data[key] is None or len(str(data[key])) == 0:
        continue
      elif key == "postData":
        if len(strToSign) > 0:
          strToSign += "||"
        strToSign += key + "=" + self._mobile_hash(data[key])
      else:
        if len(strToSign) > 0:
          strToSign += "||"
        strToSign += key + "=" + data[key]

    return hmac.new(bytes(self._tuya_key, "utf-8"), msg = bytes(strToSign, "utf-8"), digestmod = hashlib.sha256).hexdigest()


  def _mobile_hash(self, data):
    prehash = hashlib.md5(bytes(data, "utf-8")).hexdigest()
    return prehash[8:16] + prehash[0:8] + prehash[24:32] + prehash[16:24]


  def _handle(self, result):
    if result["success"]:
      return result["result"]
    elif result["errorCode"] == "USER_SESSION_INVALID":
      raise InvalidUserSession
    elif result["errorCode"] == "USER_PASSWD_WRONG":
      raise InvalidAuthentication
    else:
      logger.error("Error! Code: %s, message: %s, result: %s", result["errorCode"], result["errorMsg"], result)
      raise ValueError("Invalid result, check logs")


  def login(self):
    token_info = self._api({"action": "tuya.m.user.email.token.create"}, {"countryCode": self._country_code, "email": self._email}, requires_sid=False, do_not_relogin=True)
    payload = {
      "countryCode": str(self._country_code),
      "email": self._email,
      "ifencrypt":1,
      "options":"{\"group\": 1}",
      "passwd": self._enc_password(token_info["publicKey"], token_info["exponent"], self._password),
      "token": token_info["token"],
    }
    login_info = self._api({"action": "tuya.m.user.email.password.login"}, payload, requires_sid=False, do_not_relogin=True)
    self.sid = login_info["sid"]
  

  def _enc_password(self, public_key, exponent, password):
    key = new_textbook_rsa(RSA.construct((int(public_key), int(exponent))))
    a = "0000000000000000000000000000000000000000000000000000000000000000" + key.encrypt(hashlib.md5(password.encode("utf8")).hexdigest().encode("utf8")).hex()
    return a


  def groups(self):
    return self._api({"action": "tuya.m.location.list"})


  def devices(self, group_id):
    devs = []
    for dev in self._api({"action": "tuya.m.my.group.device.list", "gid": group_id}):
      dev_obj = self.device(dev["devId"])
      if dev_obj is not None:
        devs.append(dev_obj)
    return devs


  def device(self, device_id):
    return TuyaDevice(self, self._device_info(device_id))

  
  def _device_info(self, device_id):
    return self._api({"action": "tuya.m.device.get"}, {"devId": device_id})


  def get_dps(self, device_id, dps=None):
    result = self._api({"action": "tuya.m.device.dp.get"}, {"devId": device_id})
    if dps is not None:
      return result[dps]
    else:
      return result


  def set_dps(self, device_id, gateway_id, dps):
    return self._api(
      {"action": "tuya.m.device.dp.publish"},
      {"devId": device_id, "gwId": gateway_id, "dps": json.dumps(dps)}
    )


  def ir_children(self, parent_id):
    subdevs = []
    devices = self._api({"action": "tuya.m.device.sub.list"}, {"meshId": parent_id})
    for subdev in devices:
      subdevs.append(TuyaDevice(self, self._device_info(subdev["devId"]), gateway_id=parent_id))
    return subdevs


  def ir_get_buttons(self, gateway_id, device_id):
    record = self._api({"action": "tuya.m.infrared.record.get"}, {"devId": device_id, "gwId": device_id, "subDevId": device_id, "vender": IR_VENDOR})
    if "exts" in record and json.loads(record["exts"])["study"] == 1:
      return self._ir_learned_buttons(gateway_id, device_id)
    else:
      return self._ir_keydata_buttons(record)
  

  def _ir_learned_buttons(self, gateway_id, device_id):
    buttons = self._api(
      {"action": "tuya.m.infrared.learn.get"},
      {"devId": gateway_id, "gwId": gateway_id, "subDevId": device_id, "vender": IR_VENDOR}
    )

    return list({
      "name": button["keyName"],
      "learned": True,
      "info": {
        "keyCode": button["compressPulse"],
        "frequency": button["frequency"],
        "repeat": button["repeat"]
      },
      "dps": {
        "1": "study_key",
        "3": "",
        "7": base64.encodebytes(long_to_bytes(int(button["compressPulse"], 16))).decode("latin1").replace("\n", ""),
      }
    } for button in buttons)


  def _ir_keydata_buttons(self, record):
    buttons = self._api(
      {"action": "tuya.m.infrared.keydata.get"},
      {"devId": record["devId"], "devTypeId": str(record["devTypeId"]), "gwId": record["gwId"], "remoteId": str(record["remoteId"]), "vender": IR_VENDOR}
    )

    if "compressPulseList" not in buttons:
      return []

    return list({
      "name": button["keyName"],
      "learned": False,
      "info": {
        "keyCode": button["compressPulse"],
        "irCode": json.loads(button["exts"])["99999"],
      },
      "dps": {
        "1": "send_ir",
        "3": json.loads(button["exts"])["99999"],
        "4": button["compressPulse"],
        "10": 300, # TODO: this shouldn't be hard-coded.
        "13": 0,
      }
    } for button in buttons["compressPulseList"])
