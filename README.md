pip3 install git+https://github.com/xiangxn/nulspy.git

```
from nulspy.nuls import NULS

nuls = NULS("http://beta.public1.nuls.io", "private key")

hash = await nuls.transfer("tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh", "tNULSeBaMsJmAAAo6ooXu3QHnQCNcmjv6JyBix", 100000, "memo")
print(hash)
result = await nuls.api.getTx(hash)
print(result)
```