# -*- coding: utf-8 -*-
#
# ===================================================================
# Textbook RSA - Encryption only
#
# This code is a simple modification of the PKCS#1 OAEP code available
# on the PyCryptoome. The reason this exists is because Tuya's API is
# (unfortunately) using a textbook RSA implementation, even though it
# is considered unsecure.
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

from Crypto.Signature.pss import MGF1
import Crypto.Hash.SHA1

from Crypto.Util.py3compat import bord, _copy_bytes
import Crypto.Util.number
from   Crypto.Util.number import ceil_div, bytes_to_long, long_to_bytes
from   Crypto.Util.strxor import strxor
from Crypto import Random

import struct

class TextBookRSA:
    def __init__(self, key, hashAlgo, mgfunc, label, randfunc):
        self._key = key

        if hashAlgo:
            self._hashObj = hashAlgo
        else:
            self._hashObj = Crypto.Hash.SHA1

        if mgfunc:
            self._mgf = mgfunc
        else:
            self._mgf = lambda x,y: MGF1(x,y,self._hashObj)

        self._label = _copy_bytes(None, None, label)
        self._randfunc = randfunc


    def can_encrypt(self):
        return self._key.can_encrypt()


    def can_decrypt(self):
        return False


    def encrypt(self, message):
        message_bytes = bytes_to_long(message)
        message_powed = pow(message_bytes, self._key.e, self._key.n)
        return long_to_bytes(message_powed)


    def decrypt(self, ciphertext):
        raise NotImplementedError("This is not implemented (we don't need it here)")


def new(key, hashAlgo=None, mgfunc=None, label=b'', randfunc=None):
    if randfunc is None:
        randfunc = Random.get_random_bytes
    return TextBookRSA(key, hashAlgo, mgfunc, label, randfunc)
