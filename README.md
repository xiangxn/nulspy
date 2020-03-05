transfer:
```
outputs = [{
        "address": "tNULSeBaMsJmAAAo6ooXu3QHnQCNcmjv6JyBix",
        "amount": 100000,
        "lockTime": 0,
        "assetsChainId": 2,
        "assetsId": 1
        }]
tx = await Transaction.fromDict({
    "type": 2,
    "time": int(time.time()),
    "remark": "p:36893488157591172662".encode('utf-8'), #p:36893488157591172661
    "coinFroms": [{
        'address': "tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh",
        'assetsChainId': 2,
        'assetsId': 1,
        'amount': 0,
        'nonce': "a5471e8fe27db3af",
        'locked': 0
    }],
    "coinTos": outputs
})
tx.inputs[0]['amount'] = ((await tx.calculateFee()) + sum([o['amount'] for o in outputs]))
priKey = bytes.fromhex("private key")
print(len(priKey))
await tx.signTx(priKey)
tx_hex = (await tx.serialize()).hex()
print(tx_hex)
```