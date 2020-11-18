import asyncio
import aiohttp
import json
from ..define import Define


class RpcAPI:
    def __init__(self, url, chain_id, address_prefix=None):
        self.url = url
        self.chain_id = chain_id
        self.asset_id = 1
        if not address_prefix:
            self.address_prefix = Define.NETWORKS[chain_id]
        else:
            self.address_prefix = address_prefix
        self.headers = {'User-Agent': 'curl/7.35.0', 'Accept': '*/*', 'Content-Type': 'application/json;charset=UTF-8'}
        self.proc_id = 0

    def _get_next_id(self):
        self.proc_id += 1
        return self.proc_id

    async def _post(self, json, timeout=30):
        result = None
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(self.url, json=json, timeout=timeout) as res:
                    if res.status == 200 or res.status == 202:
                        result = await res.json()
                        if "result" in result:
                            result = result['result']
                        elif "error" in result:
                            print("api error:", result['error']['message'])
                            result = None
            except Exception as e:
                pass
        return result

    def _create_pars(self, method, pars=[]):
        data = {"jsonrpc": "2.0", "method": method, "params": pars, "id": self._get_next_id()}
        return data

    def _get_chain_id(self, chain_id):
        cid = chain_id
        if not cid:
            cid = self.chain_id
        return cid

    async def getChainInfo(self):
        pars = self._create_pars("getChainInfo")
        result = await self._post(pars)
        if result:
            self.chain_id = result['chainId']
            self.asset_id = result['defaultAsset']['assetId']
            #self.address_prefix = result['addressPrefix']
        return result

    async def getInfo(self):
        pars = self._create_pars("getInfo", [self.chain_id])
        result = await self._post(pars)
        if result:
            self.chain_id = result['chainId']
            self.asset_id = result['defaultAsset']['assetId']
            #self.address_prefix = result['addressPrefix']
        return result

    async def getBalance(self, addr, asset_chain=2, asset=1):
        assert addr.startswith(self.address_prefix), "Invalid addr"
        pars = self._create_pars("getAccountBalance", [self.chain_id, asset_chain, asset, addr])
        result = await self._post(pars)
        return result

    async def getTx(self, trx_id):
        pars = self._create_pars("getTx", [self.chain_id, trx_id])
        result = await self._post(pars)
        return result

    async def getAccountTxs(self, addr, page=1, page_size=10, tx_type=2, start_block=-1, end_block=-1, asset_chainId=0, asset_id=0):
        pars = self._create_pars("getAccountTxs", [self.chain_id, page, page_size, addr, tx_type, start_block, end_block, asset_chainId, asset_id])
        result = await self._post(pars)
        return result

    async def broadcast(self, tx_hex):
        pars = self._create_pars("broadcastTx", [self.chain_id, tx_hex])
        result = await self._post(pars)
        return result

    async def estimateContractCallGas(self, addr, contractAddress, methodName, value=0, args=[], methodDesc=None, chain_id=None):
        pars = self._create_pars("imputedContractCallGas", [self._get_chain_id(chain_id), addr, value, contractAddress, methodName, methodDesc, args])
        result = await self._post(pars)
        return result

    async def invokeView(self, contractAddress, methodName, methodDesc=None, args=[], chainId=None):
        pars = self._create_pars("invokeView", [self._get_chain_id(chainId), contractAddress, methodName, methodDesc, args])
        return await self._post(pars)

    async def getContractMethodArgsTypes(self, contractAddress, methodName, methodDesc, chainId=None):
        pars = self._create_pars("getContractMethodArgsTypes", [self._get_chain_id(chainId), contractAddress, methodName, methodDesc])
        return await self._post(pars)

    async def contractCallOffline(self,
                                  sender,
                                  senderBalance,
                                  nonce,
                                  contractAddress,
                                  gasLimit,
                                  methodName,
                                  value=0,
                                  methodDesc=None,
                                  args=[],
                                  argsType=[],
                                  remark=None,
                                  chain_id=None):
        pars = self._create_pars(
            "contractCallOffline",
            [self._get_chain_id(chain_id), sender, senderBalance, nonce, value, contractAddress, gasLimit, methodName, methodDesc, args, argsType, remark])
        print("pars: ", pars)
        return await self._post(pars)
