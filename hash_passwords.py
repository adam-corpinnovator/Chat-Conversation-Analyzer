#!/usr/bin/env python3
"""
Password hashing utility for streamlit-authenticator
Run this script to generate hashed passwords for your config.yaml file
"""

import streamlit_authenticator as stauth

def main():
    print("=== Password Hashing Utility ===")
    print("Generate hashed passwords for your streamlit-authenticator config\n")
    
    # Default passwords to hash
    passwords_to_hash = {
        'admin123': 'Default admin password',
        'user123': 'Default user password',
        'demo123': 'Demo password'
    }
    
    print("Hashing default passwords:")
    print("-" * 50)
    
    for password, description in passwords_to_hash.items():
        hashed = stauth.Hasher.hash(password)
        print(f"{description}:")
        print(f"  Plain: {password}")
        print(f"  Hash:  {hashed}")
        print()
    
    # Interactive mode
    print("Interactive mode - Enter custom passwords to hash:")
    print("(Press Enter with empty password to exit)")
    print("-" * 50)
    
    while True:
        password = input("Enter password to hash (or press Enter to exit): ").strip()
        if not password:
            break
        
        hashed = stauth.Hasher.hash(password)
        print(f"Hashed password: {hashed}")
        print()
    
    print("Done! Copy the hashed passwords to your config.yaml file.")

if __name__ == "__main__":
    main()
