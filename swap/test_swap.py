import swap_util
wallet_address = '' #钱包地址
token_contract = "0x55d398326f99059ff775485246999027b3197955"  #代币合约地址
private_key = '' #私钥

swap_bnb_for_token_amount = 0.001 #买入多少bnb的token
swap_token_for_bnb_amount = 0.3 #卖出多少token

wbnb = swap_util.get_wbnb_balance(wallet_address)
contract = swap_util.get_contract(token_contract)
print("BNB balance:", "", wbnb)

token_balance = swap_util.get_token_balance(wallet_address, contract, 1)
token_name = swap_util.get_token_info(contract)[1]
print("Token name:", token_name, ", token balance:", token_balance)

token_price = swap_util.fetch_token_buy_price_as_bnb(token_contract, contract)
print("Token name:", token_name,", token price:", token_price, '/bnb')

receipt = swap_util.buy(wallet_address,token_contract, swap_bnb_for_token_amount, private_key)
print(receipt)

receipt = swap_util.sell(wallet_address, token_contract, swap_token_for_bnb_amount, private_key)
print(receipt)
