import asyncio
import aiohttp

class RpcAPI:
    def __init__(self, url, chain_id, address_prefix = "tNULS"):
        self.url = url
        self.chain_id = chain_id
        self.asset_id = 1
        self.address_prefix = address_prefix
        self.headers = {'User-Agent': 'curl/7.35.0', 'Accept': '*/*','Content-Type': 'application/json;charset=UTF-8'}
        self.proc_id = 0
        
    def _get_next_id(self):
        self.proc_id += 1
        return self.proc_id
        
    async def _post(self, json, timeout = 30):
        result = None
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(self.url, json = json, timeout = timeout) as res:
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
        data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": pars,  
                "id": self._get_next_id()
        }
        return data
    
    async def getInfo(self):
        pars = self._create_pars("getChainInfo")
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
    
    async def getAccountTxs(self, addr, page=1, page_size=10, tx_type=2, start_block=-1, end_block=-1):
        pars = self._create_pars("getAccountTxs", [self.chain_id, page, page_size, addr, tx_type, start_block, end_block])
        result = await self._post(pars)
        return result
    
    async def broadcast(self, tx_hex):
        pars = self._create_pars("broadcastTx", [self.chain_id, tx_hex])
        result = await self._post(pars)
        return result
        
        