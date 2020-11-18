import sys
sys.path.append('../nulspy')

import time
from nulspy.transaction import Transaction
from nulspy.nuls import NULS
from nulspy.address import Address
from coincurve import PrivateKey, PublicKey


class TestKeys:
    def test_convert(self):
        k = "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4"
        priv = PrivateKey(bytes.fromhex(k))
        print("addr: ", Address.getAddress(priv.public_key.format(), chain_id=2))
        
