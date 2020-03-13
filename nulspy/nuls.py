from .api.rpc_api import RpcAPI
from .transaction import Transaction
import time

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
        
    async def transfer(self, from_addr, to_addr, amount, memo="", asset_id=1, asset_chain_id=2):
        nonce = ""
        balance = await self.api.getBalance(from_addr, asset_chain=asset_chain_id, asset=asset_id)
        assert balance, "Failed to get balance"
        nonce = balance['nonce']
        outputs = [{
            "address": to_addr,
            "amount": amount,
            "lockTime": 0,
            "assetsChainId": asset_chain_id,
            "assetsId": asset_id
            }]
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
        