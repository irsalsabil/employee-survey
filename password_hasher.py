import streamlit_authenticator as stauth

# Define plain-text passwords
passwords = ['abc']

# Generate hashed passwords
hashed_passwords = stauth.Hasher(passwords).generate()

# Print the hashed passwords
print(hashed_passwords)

# Check

import bcrypt

# Simulated login password
login_password = 'x'  # Replace with actual password

# Hashed password from df_creds
hashed_password_from_db = "$2b$12$.."  # Example

# Check if the entered password matches the stored hash
if bcrypt.checkpw(login_password.encode('utf-8'), hashed_password_from_db.encode('utf-8')):
    print("Password match!")
else:
    print("Password incorrect.")