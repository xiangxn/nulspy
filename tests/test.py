import sys
sys.path.append('../nulspy')

import time
import asyncio
from nulspy.transaction import Transaction

loop = asyncio.get_event_loop()

async def run_test():
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
    priKey = bytes.fromhex("21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4")
    print(len(priKey))
    await tx.signTx(priKey)
    tx_hex = (await tx.serialize()).hex()
    print(tx_hex)

loop.run_until_complete(asyncio.wait([loop.create_task(run_test())]))
loop.run_forever()
loop.close()

