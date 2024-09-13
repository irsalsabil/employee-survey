import streamlit_authenticator as stauth

# Define plain-text passwords
passwords = ['abc', 'def']

# Generate hashed passwords
hashed_passwords = stauth.Hasher(passwords).generate()

# Print the hashed passwords
print(hashed_passwords)

