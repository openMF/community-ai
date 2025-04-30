import json
import os
import random
from datetime import datetime, timedelta

# Path to mock database
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/mock_db.json')

def load_mock_db():
    """Load mock database or create if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Create a mock database with sample data
        mock_db = {
            'users': {
                '1': {
                    'id': '1',
                    'name': 'John Doe',
                    'accounts': {
                        'savings': {
                            'account_id': 'SAV12345',
                            'balance': 5000.00,
                            'currency': 'USD'
                        },
                        'checking': {
                            'account_id': 'CHK67890',
                            'balance': 1200.50,
                            'currency': 'USD'
                        }
                    },
                    'transactions': generate_mock_transactions('1')
                },
                '2': {
                    'id': '2',
                    'name': 'Jane Smith',
                    'accounts': {
                        'savings': {
                            'account_id': 'SAV54321',
                            'balance': 8500.75,
                            'currency': 'USD'
                        }
                    },
                    'transactions': generate_mock_transactions('2')
                }
            }
        }
        
        with open(DB_PATH, 'w') as f:
            json.dump(mock_db, f, indent=2)
    
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_mock_db(db):
    """Save changes to mock database."""
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

def generate_mock_transactions(user_id, count=10):
    """Generate mock transaction history for demo purposes."""
    transaction_types = ['deposit', 'withdrawal', 'transfer_in', 'transfer_out', 'payment']
    transactions = []
    
    for i in range(count):
        transaction_type = random.choice(transaction_types)
        amount = round(random.uniform(10, 500), 2)
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        transaction = {
            'transaction_id': f'T{user_id}{i}',
            'type': transaction_type,
            'amount': amount,
            'date': date,
            'description': f'{transaction_type.replace("_", " ").title()} of ${amount}'
        }
        
        if transaction_type in ['transfer_in', 'transfer_out']:
            transaction['counterparty'] = f'User{random.randint(1, 5)}'
            
        transactions.append(transaction)
    
    return sorted(transactions, key=lambda x: x['date'], reverse=True)

def process_banking_request(intent_data, user):
    """
    Process banking requests based on the intent.
    This is a simplified version for the POC.
    """
    intent_type = intent_data['intent_type']
    parameters = intent_data['parameters']
    
    # Load the mock database
    db = load_mock_db()
    user_data = db['users'].get(user['id'])
    
    if not user_data:
        return {'error': 'User not found'}
    
    response = {
        'success': True,
        'intent_type': intent_type,
    }
    
    if intent_type == 'check_balance':
        response['accounts'] = user_data['accounts']
        response['message'] = f"Your current balances are: "
        for acc_type, acc_data in user_data['accounts'].items():
            response['message'] += f"{acc_type}: {acc_data['balance']} {acc_data['currency']}, "
        response['message'] = response['message'].rstrip(', ')
    
    elif intent_type == 'transfer_money':
        if 'amount' not in parameters:
            return {'error': 'Amount not specified', 'success': False}
            
        amount = parameters['amount']
        recipient = parameters.get('recipient', 'unknown')
        
        # Find recipient in our mock DB (simplified)
        recipient_id = None
        for uid, udata in db['users'].items():
            if recipient.lower() in udata['name'].lower():
                recipient_id = uid
                break
        
        if not recipient_id:
            return {'error': f'Recipient {recipient} not found', 'success': False}
            
        # Check if sufficient funds (from first available account)
        source_account = next(iter(user_data['accounts'].values()))
        if source_account['balance'] < amount:
            return {'error': 'Insufficient funds', 'success': False}
            
        # Update balances
        source_account['balance'] -= amount
        db['users'][recipient_id]['accounts'][next(iter(db['users'][recipient_id]['accounts']))]['balance'] += amount
        
        # Add transaction records
        timestamp = datetime.now().strftime('%Y-%m-%d')
        tx_id = f"TX{timestamp.replace('-', '')}{random.randint(1000, 9999)}"
        
        # Add to sender's transactions
        user_data['transactions'].insert(0, {
            'transaction_id': tx_id,
            'type': 'transfer_out',
            'amount': amount,
            'date': timestamp,
            'description': f'Transfer to {recipient}',
            'counterparty': recipient
        })
        
        # Add to recipient's transactions
        db['users'][recipient_id]['transactions'].insert(0, {
            'transaction_id': tx_id,
            'type': 'transfer_in',
            'amount': amount,
            'date': timestamp,
            'description': f'Transfer from {user_data["name"]}',
            'counterparty': user_data['name']
        })
        
        save_mock_db(db)
        response['message'] = f"Successfully transferred {amount} to {recipient}"
        response['new_balance'] = source_account['balance']
    
    elif intent_type == 'transaction_history':
        period = parameters.get('period', 'recent')
        transactions = user_data['transactions']
        
        if period == 'last_week':
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            transactions = [t for t in transactions if t['date'] >= one_week_ago]
        elif period == 'last_month':
            one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            transactions = [t for t in transactions if t['date'] >= one_month_ago]
        
        response['transactions'] = transactions[:5]  # Limit to 5 for demo
        response['message'] = f"Here are your recent transactions"
    
    else:
        response = {
            'success': False,
            'message': "I'm sorry, I don't understand that banking request."
        }
    
    return response
