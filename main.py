import streamlit as st
import pandas as pd
import sqlite3
from streamlit_authenticator import Authenticate

# Connect to SQLite database
conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

# Create a user database
def create_user_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    conn.commit()

# Create the main database for trains
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT)")
    conn.commit()

create_user_db()
create_db()

# User authentication setup
def get_usernames():
    c.execute("SELECT username FROM users")
    return [row[0] for row in c.fetchall()]

def sign_up(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("Signup successful! Please log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

# Authentication function
def auth_user():
    usernames = get_usernames()
    authenticator = Authenticate(usernames, "my_app", "my_app", "password", "user")
    return authenticator.login("Login", "main")

# Set a background image
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url('https://your-image-url.jpg');
            background-size: cover;
            background-position: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Your existing functions go here...

# Main app function
def main():
    set_background()
    st.title("Railway Management System")

    # Authentication
    if auth_user():
        st.success("Logged in successfully!")

        operation = st.selectbox(
            "Choose Operation",
            [
                "Add Train",
                "Cancel Train",
                "Delete Train",
                "View Seats",
                "Book Tickets",
                "Search Train",
                "Allocate Seat",
                "Chat with Bot"
            ]
        )
        
        if operation == "Add Train":
            with st.form(key='add_train_form'):
                train_name = st.text_input("Train Name", key='train_name')
                train_number = st.text_input("Train Number", key='train_number')
                submit_button = st.form_submit_button(label="Add Train")

                if submit_button:
                    add_train(train_name, train_number)
        
        elif operation == "Cancel Train":
            with st.form(key='cancel_train_form'):
                train_number = st.text_input("Train Number", key='cancel_train_number')
                submit_button = st.form_submit_button(label="Cancel Train")

                if submit_button:
                    cancel_train(train_number)

        # Add other operations similar to the above...

    else:
        st.subheader("Signup")
        with st.form(key='signup_form'):
            new_username = st.text_input("Username", key='new_username')
            new_password = st.text_input("Password", type="password", key='new_password')
            submit_button = st.form_submit_button(label="Sign Up")

            if submit_button:
                sign_up(new_username, new_password)

        st.subheader("Or Log In")
        with st.form(key='login_form'):
            username = st.text_input("Username", key='username')
            password = st.text_input("Password", type="password", key='password')
            submit_button = st.form_submit_button(label="Log In")

            if submit_button:
                if login(username, password):
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid credentials.")

if __name__ == "__main__":
    main()
