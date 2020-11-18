import sys
sys.path.append('../nulspy')

import time
import asyncio
from nulspy.transaction import Transaction
from nulspy.nuls import NULS
from coincurve import PrivateKey, PublicKey

loop = asyncio.get_event_loop()
nuls = NULS("http://beta.public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4")


async def run_test():
    hash = await nuls.transfer("tNULSeBaMfn8mwR6THZoGzCgDCx3oeLnT1TsKh", "tNULSeBaMsJmAAAo6ooXu3QHnQCNcmjv6JyBix", 100000, "p:36893488157591172661")
    print(hash)
    result = await nuls.api.getTx(hash)
    print(result)


async def getInfos():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    result = await n.api.getInfo()
    print("getInfo: ", result)
    result = await n.api.getBalance("NULSd6HgXSXbLcrp1YAMr76YFHVpMzCCeWLc2")
    print("getBalance: ", result)
    result = await n.api.getAccountTxs("NULSd6HgXSXbLcrp1YAMr76YFHVpMzCCeWLc2")
    print("txs: ", result)


async def estimateGas():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    m = await n.estimateContractCallGas("NULSd6HgwJmD4SC1NAJXu8tC6NKsWs99P2jpw",
                                        "approve",
                                        methodDesc="(Address spender, BigInteger value) return boolean",
                                        args=["NULSd6Hgz6suLcHCxfLoYTp3AfdQzwKRCX89B", "2800000000"],
                                        addr="NULSd6HgjUSxvAUyJDTUKu8enCykSwA6LeuAu")
    print("m: ", m)


async def invokeView():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    result = await n.invokeView("NULSd6HguK98JD4yFfjYkDTq8VXfPYDNeFMiL",
                                "earnedOf",
                                methodDesc="(String caveName, Address account) return Ljava/util/List;",
                                args=["BlackIron", "NULSd6HgXSXbLcrp1YAMr76YFHVpMzCCeWLc2"])
    print("invokeView result: ", result)


async def callContractOffline():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    price = await n.invokeView("NULSd6HgxnDFHmEHZsetY2Qjc5eX6oXH6vPzx", "getCurrentPrice", "() return BigInteger")
    print("price: ", price)
    result = await n.contractCallOffline("NULSd6HgwJmD4SC1NAJXu8tC6NKsWs99P2jpw",
                                         "approve",
                                         sender="NULSd6HgXSXbLcrp1YAMr76YFHVpMzCCeWLc2",
                                         args=["NULSd6HgxnDFHmEHZsetY2Qjc5eX6oXH6vPzx", price],
                                         methodDesc="(Address spender, BigInteger value) return boolean",
                                         argsType=["Address", "BigInteger"])
    print("callContract result: ", result)


async def getContractMethodArgsTypes():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    res = await n.api.getContractMethodArgsTypes("NULSd6HgwJmD4SC1NAJXu8tC6NKsWs99P2jpw", "approve", "(Address spender, BigInteger value) return boolean")
    print("res: ", res)


async def callContract():
    n = NULS("https://public1.nuls.io", "21a69261f69f7194a771849b5aebcae95e415156097dc25648f621c7874bfac4", chain_id=1)
    data = {
        'contractAddress': "NULSd6HgvBGqSQBr49QmB9BJia4RnzsAWpjtE",
        'value': 0,
        'chainId': n.chain_id,
        'methodName': "remand",
        'methodDesc': "(String contractAddress, BigInteger tokenId, String doing) return void",
        'args': ["NULSd6Hgr5k9ic8kxr9UnPmiCqaHxcypimHex", "16365", "minelp"]
    }
    res = await n.callContract("NULSd6HgXSXbLcrp1YAMr76YFHVpMzCCeWLc2", data)
    print("res: ", res)


def getTasks(loop):
    tasks = []
    # tasks += [loop.create_task(run_test())]
    # tasks += [loop.create_task(getInfos())]
    # tasks += [loop.create_task(estimateGas())]
    # tasks += [loop.create_task(invokeView())]
    # tasks += [loop.create_task(callContractOffline())]
    # tasks += [loop.create_task(getContractMethodArgsTypes())]
    tasks += [loop.create_task(callContract())]
    return tasks


loop.run_until_complete(asyncio.wait(getTasks(loop)))
loop.run_forever()
loop.close()
