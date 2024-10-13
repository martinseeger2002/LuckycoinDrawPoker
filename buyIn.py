import configparser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

# Load RPC credentials from RPC.conf
config = configparser.ConfigParser()
config.read('RPC.conf')

rpc_user = config['rpcconfig']['rpcuser']
rpc_password = config['rpcconfig']['rpcpassword']
rpc_host = config['rpcconfig']['rpchost']
rpc_port = config['rpcconfig']['rpcport']

# Create a connection to the Litecoin RPC server
def create_rpc_connection():
    return AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

rpc_connection = create_rpc_connection()

# Define the recipient address (update with your recipient address)
recipient_address = "<player pool address>"

def process_transaction(from_address, amount_ltc):
    try:
        # Set up transaction details
        to_address = recipient_address
        amount = Decimal(str(amount_ltc))
        
        # List unspent transactions for the from_address
        unspent_txs = rpc_connection.listunspent(0, 9999999, [from_address])
        
        # Calculate the total amount of UTXOs available
        total_available = sum(utxo['amount'] for utxo in unspent_txs)
        
        if total_available < amount:
            print("Insufficient funds.")
            return None
        
        # Create a raw transaction using UTXOs from the from_address
        inputs = [{"txid": utxo['txid'], "vout": utxo['vout']} for utxo in unspent_txs]
        amount_to_send = {to_address: float(amount)}
        
        raw_tx = rpc_connection.createrawtransaction(inputs, amount_to_send)
        
        # Fund the transaction, specifying the change address
        funded_tx = rpc_connection.fundrawtransaction(raw_tx, {"changeAddress": from_address})
        funded_tx_hex = funded_tx['hex']
        
        # Sign the transaction
        try:
            signed_tx = rpc_connection.signrawtransactionwithwallet(funded_tx_hex)
        except JSONRPCException as e:
            if e.error['code'] == -32601:  # Method not found
                signed_tx = rpc_connection.signrawtransaction(funded_tx_hex)
        
        if not signed_tx['complete']:
            print("Transaction signing incomplete.")
            return None
        signed_tx_hex = signed_tx['hex']
        
        # Broadcast the transaction
        txid = rpc_connection.sendrawtransaction(signed_tx_hex)
        print(f"Transaction broadcasted successfully! TXID: {txid}")
        return txid
        
    except JSONRPCException as e:
        print(f"An error occurred: {e.error['message']}")
        return None

# Example usage
if __name__ == "__main__":
    from_address = "<from address>"  # Replace with your Litecoin address
    amount_ltc = 50.0  # The amount you want to send in Litecoin

    txid = process_transaction(from_address, amount_ltc)
    if txid:
        print(f"Transaction successful. TXID: {txid}")
    else:
        print("Transaction failed.")
