import streamlit as st
import sqlite3
import hashlib
import os
from cryptography.fernet import Fernet

KEY_FILE = "simple_secret_key"

def generate_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

cipher = Fernet(generate_key())

def init_db():
    conn = sqlite3.connect("simple_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            label TEXT PRIMARY KEY,
            encrypted_secret TEXT NOT NULL,
            passkey TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ✅ Call the DB initialization
init_db()

def hash_password(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

# Streamlit UI
st.title("🧠💾 Memory Vault: Where Secrets Sleep Securely")
st.subheader("Encrypt once. Retrieve when needed.")

menu = ["Store Secret", "Retrieve Secret"]
choice = st.sidebar.selectbox("Select an option", menu)

if choice == "Store Secret":
    st.subheader("Store your secret")

    label = st.text_input("Label (Unique ID): ")
    secret = st.text_area("Secret (Text): ")
    passkey = st.text_input("Passkey (Password): ", type="password")

    if st.button("Encrypt and Save"):
        if label and secret and passkey:
            conn = sqlite3.connect("simple_data.db")
            cursor = conn.cursor()

            encrypted_secret = encrypt(secret)
            hashed_passkey = hash_password(passkey)

            try:
                cursor.execute("INSERT INTO users (label, encrypted_secret, passkey) VALUES (?, ?, ?)",
                               (label, encrypted_secret, hashed_passkey))
                conn.commit()
                st.success("✅ Secret stored successfully!")
            except sqlite3.IntegrityError:
                st.error("❌ Label already exists. Please choose a different one.")
            finally:
                conn.close()
        else:
            st.warning("⚠️ Please fill all the fields.")

elif choice == "Retrieve Secret":
    st.subheader("Retrieve a stored secret")

    label = st.text_input("Enter label of the secret: ")
    passkey = st.text_input("Enter passkey: ", type="password")

    if st.button("Decrypt and Retrieve"):
        conn = sqlite3.connect("simple_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_secret, passkey FROM users WHERE label = ?", (label,))
        result = cursor.fetchone()
        conn.close()

        if result:
            encrypted_secret, hashed_passkey = result
            if hash_password(passkey) == hashed_passkey:
                decrypted_secret = decrypt(encrypted_secret)
                st.success(f"🔓 Your secret: {decrypted_secret}")
            else:
                st.error("❌ Incorrect passkey.")
        else:
            st.error("❌ Label not found.")
