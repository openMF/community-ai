"""
This script updates the existing JSON database files to ensure they contain
all three demo users (John, Jane, and Jacob) with their accounts and transactions.
Run this once after cloning the repository to ensure consistent demo data.
"""

import os
import json
import sys
from werkzeug.security import generate_password_hash
from services.banking_service import generate_mock_transactions

# Path to database files
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.json')
MOCK_DB_PATH = os.path.join(DATA_DIR, 'mock_db.json')

def ensure_data_directory():
    """Ensure data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory: {DATA_DIR}")

def update_users_db():
    """Update or create the users database file."""
    # Define demo users
    users = {
        '1': {
            'id': '1',
            'username': 'johndoe',
            'password_hash': generate_password_hash('password123'),
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'language': 'en-US'
        },
        '2': {
            'id': '2',
            'username': 'janesmith',
            'password_hash': generate_password_hash('password456'),
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '+0987654321',
            'language': 'hi-IN'
        },
        '3': {
            'id': '3',
            'username': 'jacobbrown',
            'password_hash': generate_password_hash('password789'),
            'name': 'Jacob Brown',
            'email': 'jacob@example.com',
            'phone': '+1122334455',
            'language': 'ta-IN'
        }
    }
    
    # Write to file
    with open(USERS_DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"Updated users database: {USERS_DB_PATH}")
    return users

def update_mock_db():
    """Update or create the mock banking database file."""
    # Define mock banking data
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
            },
            '3': {
                'id': '3',
                'name': 'Jacob Brown',
                'accounts': {
                    'savings': {
                        'account_id': 'SAV98765',
                        'balance': 3200.50,
                        'currency': 'USD'
                    },
                    'investment': {
                        'account_id': 'INV12345',
                        'balance': 10000.00,
                        'currency': 'USD'
                    }
                },
                'transactions': generate_mock_transactions('3')
            }
        }
    }
    
    # Write to file
    with open(MOCK_DB_PATH, 'w') as f:
        json.dump(mock_db, f, indent=2)
    
    print(f"Updated mock database: {MOCK_DB_PATH}")

def main():
    """Main function to update all database files."""
    try:
        print("Starting database update...")
        
        # Ensure data directory exists
        ensure_data_directory()
        
        # Update users database
        update_users_db()
        
        # Update mock banking database
        update_mock_db()
        
        print("Database update completed successfully!")
        
    except Exception as e:
        print(f"Error updating databases: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
