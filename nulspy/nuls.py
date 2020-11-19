from .api.rpc_api import RpcAPI
from coincurve import PrivateKey, PublicKey
from .transaction import Transaction
from .address import Address
from .define import Define
import nulspy.trxs.contract
import time
import math


class NULS:
    def __init__(self, api_url, private_key, chain_id=2):
        self.api_url = api_url
        self.chain_id = chain_id
        self.api = RpcAPI(self.api_url, self.chain_id)
        if isinstance(private_key, bytes) and len(private_key) == 32:
            self.private_key = private_key
        else:
            assert len(private_key) == 64, "Invalid private key"
            self.private_key = bytes.fromhex(private_key)

    async def countFee(self, tx, signatrueCount):
        data = await tx.serialize()
        txSize = len(data)
        txSize = txSize + signatrueCount * 110
        return 100000 * math.ceil(txSize / 1024)

    def twoDimensionalArray(self, args, argsType):
        if not args or len(args) == 0:
            return None
        elif len(args) != len(argsType):
            raise ValueError("args number error")
        else:
            two = []
            for i in range(len(args)):
                arg = args[i]
                if not arg:
                    two.append([])
                    continue
                if isinstance(arg, str):
                    if argsType and not arg and not isinstance(argsType[i], str):
                        two.append([])
                    elif not argsType and arg and "[]" in argsType[i]:
                        arrArg = eval(arg)
                        if isinstance(arrArg, list):
                            ma = []
                            for k in range(len(arrArg)):
                                ma.append(str(arrArg[k]))
                            two.append(ma)
                        else:
                            raise ValueError("args number error")
                    else:
                        two.append([arg])
                elif isinstance(arg, list):
                    mb = []
                    for n in range(len(arg)):
                        mb.append(str(arg[n]))
                    two.append(mb)
                else:
                    two.append([str(arg)])
            return two

    async def transfer(self, from_addr, to_addr, amount, memo="", asset_id=1, asset_chain_id=2):
        nonce = ""
        balance = await self.api.getBalance(from_addr, asset_chain=asset_chain_id, asset=asset_id)
        assert balance, "Failed to get balance"
        nonce = balance['nonce']
        outputs = [{"address": to_addr, "amount": amount, "lockTime": 0, "assetsChainId": asset_chain_id, "assetsId": asset_id}]
        tx = await Transaction.fromDict({
            "type": 2,
            "time": int(time.time()),
            "remark": memo.encode('utf-8'),
            "coinFroms": [{
                'address': from_addr,
                'assetsChainId': asset_chain_id,
                'assetsId': asset_id,
                'amount': 0,
                'nonce': nonce,
                'locked': 0
            }],
            "coinTos": outputs
        })
        tx.inputs[0]['amount'] = ((await tx.calculateFee()) + sum([o['amount'] for o in outputs]))
        await tx.signTx(self.private_key)
        tx_hex = (await tx.serialize()).hex()
        result = await self.api.broadcast(tx_hex)
        if result and "hash" in result:
            return result['hash']
        else:
            return None

    async def estimateContractCallGas(self, contractAddress, methodName, addr=None, value=0, args=[], methodDesc=None):
        if not addr:
            addr = Address.getAddress(PrivateKey(self.private_key).public_key.format(), chain_id=self.chain_id)
        result = await self.api.estimateContractCallGas(addr, contractAddress, methodName, value=value, args=args, methodDesc=methodDesc)
        if result and "gasLimit" in result:
            return result['gasLimit']
        return 1

    async def invokeView(self, contractAddress, methodName, methodDesc=None, args=[]):
        result = await self.api.invokeView(contractAddress, methodName, methodDesc, args, self.chain_id)
        if result and "result" in result:
            return result['result']
        return None

    async def callContract(self, fromAddress, contractCall, remark="", assetsChainId=1, assetsId=1, privateKey=None):
        balanceInfo = await self.api.getBalance(fromAddress, asset_chain=self.chain_id)
        gasLimit = await self.estimateContractCallGas(contractCall['contractAddress'],
                                                      contractCall['methodName'],
                                                      value=contractCall['value'],
                                                      args=contractCall['args'],
                                                      methodDesc=contractCall['methodDesc'])

        argsType = await self.api.getContractMethodArgsTypes(contractCall['contractAddress'],
                                                             contractCall['methodName'],
                                                             contractCall['methodDesc'],
                                                             chainId=self.chain_id)
        data = {
            'chainId': self.chain_id,
            'sender': fromAddress,
            'contractAddress': contractCall['contractAddress'],
            'value': contractCall['value'],
            'gasLimit': gasLimit,
            'price': Define.CONTRACT_MINIMUM_PRICE,
            'methodName': contractCall['methodName'],
            'methodDesc': contractCall['methodDesc'],
            'args': self.twoDimensionalArray(contractCall['args'], argsType)
        }
        gasFee = gasLimit * data['price']
        amount = data['value'] + gasFee
        transferInfo = {'fromAddress': fromAddress, 'assetsChainId': assetsChainId, 'assetsId': assetsId, 'amount': amount, 'fee': 100000}

        if contractCall['value'] > 0:
            transferInfo['toAddress'] = contractCall['contractAddress']
            transferInfo['value'] = contractCall['value']
        inputs = [{
            'address': transferInfo['fromAddress'],
            'assetsChainId': transferInfo['assetsChainId'],
            'assetsId': transferInfo['assetsId'],
            'amount': transferInfo['amount'] + transferInfo['fee'],
            'locked': 0,
            'nonce': balanceInfo['nonce']
        }]
        if balanceInfo['balance'] < inputs[0]['amount']:
            raise ValueError("Your balance is not enough.")
        outputs = []
        if "toAddress" in transferInfo and transferInfo['toAddress']:
            outputs = [{
                'address': transferInfo['toAddress'],
                'assetsChainId': transferInfo['assetsChainId'],
                'assetsId': transferInfo['assetsId'],
                'amount': transferInfo['value'],
                'lockTime': 0
            }]
        tx = await Transaction.fromDict({
            "type": 16,
            "time": int(time.time()),
            "remark": remark.encode('utf-8'),
            "coinFroms": inputs,
            "coinTos": outputs,
            'txData': data
        })
        newFee = await self.countFee(tx, 1)
        if transferInfo['fee'] != newFee:
            transferInfo['fee'] = newFee
            inputs['amount'] = transferInfo['amount'] + transferInfo['fee']
            tx = await Transaction.fromDict({
                "type": 16,
                "time": int(time.time()),
                "remark": remark.encode('utf-8'),
                "coinFroms": inputs,
                "coinTos": outputs,
                'txData': data
            })
        if not privateKey:
            privateKey = self.private_key
        await tx.signTx(privateKey)
        tx_hex = (await tx.serialize()).hex()
        result = await self.api.broadcast(tx_hex)
        if result and "hash" in result:
            return result['hash']
        else:
            return None

    async def contractCallOffline(self, contractAddress, methodName, sender=None, args=[], value=0, methodDesc=None, argsType=[], remark=None):
        if not sender:
            sender = Address.getAddress(PrivateKey(self.private_key).public_key.format(), chain_id=self.chain_id)
        balance = await self.api.getBalance(sender, asset_chain=self.chain_id)
        senderBalance = balance['balance']
        nonce = balance['nonce']
        res = await self.api.estimateContractCallGas(sender, contractAddress, methodName, value=value, args=args, methodDesc=methodDesc)
        gasLimit = res['gasLimit']
        result = await self.api.contractCallOffline(sender,
                                                    senderBalance,
                                                    nonce,
                                                    contractAddress,
                                                    gasLimit,
                                                    methodName,
                                                    value=value,
                                                    methodDesc=methodDesc,
                                                    args=args,
                                                    argsType=argsType,
                                                    remark=remark,
                                                    chain_id=self.chain_id)
        if result and "txHex" in result:
            return result
        return None
