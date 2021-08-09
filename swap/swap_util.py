from web3 import Web3
import config
import time

web3 = Web3(Web3.HTTPProvider(config.BSC_URL))

def get_wbnb_balance(wallet_address):
    wbnb_blance = web3.fromWei(web3.eth.getBalance(wallet_address), 'ether')
    return wbnb_blance


def checksum(contract_address):
    return Web3.toChecksumAddress(contract_address)

def get_contract(token_contract_address, abi=config.ERC20_ABI):
    return web3.eth.contract(address=checksum(token_contract_address), abi=abi)

def get_token_info(contract):
    '获取指定代币总供应量'
    totalsupply_no_decimals = contract.functions.totalSupply().call()  #获取没有精度的总供应量
    decimals = contract.functions.decimals().call()  #获取精度
    totalsupply = float(totalsupply_no_decimals/(10**decimals))  #实际总供应量
    '获取指定代币name和symbol'
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()

    #print(name, symbol, totalsupply, decimals)
    return [name, symbol, totalsupply, decimals]

def get_token_balance(wallet, contract, humanread):
    tokenblance_no_decimals = contract.functions.balanceOf(checksum(wallet)).call()
    if humanread == 1:
        decimals = contract.functions.decimals().call()  #获取精度
        tokenblance = float(tokenblance_no_decimals/(10**decimals))
        return tokenblance
    else:
        return tokenblance_no_decimals

pancake = get_contract(config.PANCAKE_ROUTER, config.PANCAKE_ABI)

#指定bnb能兑换多少个token
def how_many_tokens_can_buy(token_contract_address, swap_bnb_amount, contract = None):
    if not contract:
        contract = get_contract(token_contract_address)
    return float(pancake.functions.getAmountsOut(web3.toWei(swap_bnb_amount, 'ether'), [checksum(config.WBNB_CONTRACT), checksum(token_contract_address)]).call()[-1])/10**get_token_info(contract)[-1]

#卖一个目标token的价格 单位为bnb
def fetch_token_sell_price_as_bnb(token_contract_address, contract = None):
    if not contract:
        contract = get_contract(token_contract_address)
    return web3.fromWei(int(pancake.functions.getAmountsOut(10**get_token_info(contract)[-1], [checksum(token_contract_address), checksum(config.WBNB_CONTRACT)]).call()[-1]), 'ether')

#买一个目标token的价格 单位为bnb
def fetch_token_buy_price_as_bnb(token_contract_address, contract = None):
    if not contract:
        contract = get_contract(token_contract_address)
    return web3.fromWei(int(pancake.functions.getAmountsIn(10**get_token_info(contract)[-1], [checksum(config.WBNB_CONTRACT), checksum(token_contract_address)]).call()[0]), 'ether')

#指定token数量能兑换多少bnb
def how_many_bnb_can_get(token_contract_address, swap_token_amount):
    price = web3.fromWei(int(pancake.functions.getAmountsOut(web3.toWei(swap_token_amount, 'ether'), [checksum(token_contract_address), checksum(config.WBNB_CONTRACT)]).call()[-1]), 'ether')
    return price


def buy(wallet_address, token_contract_address, swap_bnb_amount, private_key, slippages = config.DEFAULT_SLIPPAGE, gaslimit = config.DEFAULT_GAS_LIMIT, gasprice = config.DEFAULT_GAS_PRICE):
    contract = get_contract(token_contract_address)
    'build交易(最少获得的代币数量，[要花费的代币地址，要买的代币地址]，钱包地址，交易限制时间 当前是10min)'
    tx_info = pancake.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(int(how_many_tokens_can_buy(token_contract_address, swap_bnb_amount, contract)*(10**get_token_info(contract)[-1])*(1-slippages)), [checksum(config.WBNB_CONTRACT), checksum(token_contract_address)], wallet_address, int(time.time()) + 10 * 60). \
        buildTransaction(
        {
            'from': wallet_address,
            'value': web3.toWei(swap_bnb_amount, 'ether'),
            'gas': gaslimit,
            'gasPrice': web3.toWei(gasprice, 'Gwei'),
            'nonce': web3.eth.get_transaction_count(wallet_address),
        }
    )
    print('wbnb余额：', get_wbnb_balance(wallet_address), '目标代币余额：', get_token_balance(wallet_address, contract, 1), time.strftime("%Y-%m-%d %H:%M:%S"))
    sign_txn = web3.eth.account.sign_transaction(tx_info, private_key=private_key)
    print('交易发送中...', time.strftime("%Y-%m-%d %H:%M:%S"))
    res = web3.eth.sendRawTransaction(sign_txn.rawTransaction).hex()
    txn_receipt = web3.eth.waitForTransactionReceipt(res)
    print('Txn:', res, time.strftime("%Y-%m-%d %H:%M:%S"))
    if txn_receipt['status'] == 1:
        print('交易完成\nwbnb余额：', get_wbnb_balance(wallet_address), str(get_token_info(contract)[1])+'余额：', get_token_balance(wallet_address, contract, 1), time.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        print('交易失败，详情查看：', 'https://bscscan.com/tx/'+res)
    return txn_receipt


def check_approved(wallet_address, contract):
    print('授权检测...')
    allowance = contract.functions.allowance(checksum(wallet_address), checksum(config.PANCAKE_ROUTER)).call()
    print('授权数量：', allowance)
    return allowance


def approve(wallet_address, token_contract_address, contract = None, gaslimit = config.DEFAULT_GAS_LIMIT, gasprice = config.DEFAULT_GAS_PRICE):
    if not contract:
        contract = get_contract(token_contract_address)
    if check_approved(wallet_address, contract) < get_token_balance(wallet_address, contract, 0):
        print('代币未授权，自动授权...')
        approve_info = erc20.functions.approve(checksum(config.PANCAKE_ROUTER), int(f"0x{64 * 'f'}", 16)).buildTransaction(
            {
                'from': wallet_address,
                'value': web3.toWei(0, 'ether'),
                'gas': gaslimit,
                'gasPrice': web3.toWei(gasprice, 'Gwei'),
                'nonce': web3.eth.get_transaction_count(wallet_address),
            }
        )
        sign_txn = web3.eth.account.sign_transaction(approve_info, private_key=private_key)
        print('授权中...', time.strftime("%Y-%m-%d %H:%M:%S"))
        res = web3.eth.sendRawTransaction(sign_txn.rawTransaction).hex()
        txn_receipt = web3.eth.waitForTransactionReceipt(res)
        print('Txn:', res, time.strftime("%Y-%m-%d %H:%M:%S"))
        if txn_receipt['status'] == 1:
            print('授权完成', time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            print('授权失败，详情查看：', 'https://bscscan.com/tx/'+res)
    else:
        pass


def sell(wallet_address, token_contract_address, swap_token_amount, private_key, slippages = config.DEFAULT_SLIPPAGE, gaslimit = config.DEFAULT_GAS_LIMIT, gasprice = config.DEFAULT_GAS_PRICE):
    contract = get_contract(token_contract_address)
    approve(wallet_address, token_contract_address, contract)
    '(卖出数量, 最少收到的wbnb, [要花费的代币地址，要买的代币地址], 钱包地址，交易限制时间 当前是10min)'
    tx_info = pancake.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(int(swap_token_amount*10**get_token_info(contract)[-1]), int(web3.toWei(how_many_bnb_can_get(token_contract_address, swap_token_amount), 'ether')*(1-slippages)), [checksum(token_contract_address), checksum(config.WBNB_CONTRACT)], wallet_address, int(time.time()) + 10 * 60). \
        buildTransaction(
        {
            'from': wallet_address,
            #'value': web3.toWei(howmuchbnb, 'ether'),
            'gas': gaslimit,
            'gasPrice': web3.toWei(gasprice, 'Gwei'),
            'nonce': web3.eth.get_transaction_count(wallet_address),
        }
    )
    print('wbnb余额：', get_wbnb_balance(wallet_address), '目标代币余额：', get_token_balance(wallet_address, contract, 1), time.strftime("%Y-%m-%d %H:%M:%S"))
    sign_txn = web3.eth.account.sign_transaction(tx_info, private_key=private_key)
    print('交易发送中...', time.strftime("%Y-%m-%d %H:%M:%S"))
    res = web3.eth.sendRawTransaction(sign_txn.rawTransaction).hex()
    txn_receipt = web3.eth.waitForTransactionReceipt(res)
    print('Txn:', res, time.strftime("%Y-%m-%d %H:%M:%S"))
    if txn_receipt['status'] == 1:
        print('交易完成\nwbnb余额：', get_wbnb_balance(wallet_address), str(get_token_info(contract)[1])+'余额：', get_token_balance(wallet_address, contract, 1), time.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        print('交易失败，详情查看：', 'https://bscscan.com/tx/'+res)
    return txn_receipt


def latency():
    print('start')
    t1 = time.time_ns()
    status = web3.isConnected()
    if status is True:
        t2 = time.time_ns()
        print('Connected! Latency:', (t2-t1)/1000000, 'ms')
    else:
        print('Connect fail')