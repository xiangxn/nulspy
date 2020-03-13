import sys
sys.path.append('../nulspy')

import time
import asyncio
from nulspy.transaction import Transaction
from nulspy.nuls import NULS

loop = asyncio.get_event_loop()
nuls = NULS("http://beta.public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4")

async def run_test():
    hash = await nuls.transfer("tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh", "tNULSeBaMsJmAAAo6ooXu3QHnQCNcmjv6JyBix",
                          100000, "p:36893488157591172661")
    print(hash)
    result = await nuls.api.getTx(hash)
    print(result)
    
async def getInfos():
    
    result = await nuls.api.getInfo()
    print(result)
    result = await nuls.api.getBalance("tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh")
    print(result)
    result = await nuls.api.getAccountTxs("tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh")
    print(result)
    

def getTasks(loop):
    tasks = [loop.create_task(run_test())]
    tasks += [loop.create_task(getInfos())]
    return tasks
    

loop.run_until_complete(asyncio.wait(getTasks(loop)))
loop.run_forever()
loop.close()

