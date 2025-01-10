import streamlit as st
import sqlite3

# Establish SQLite database connection
conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

# Create necessary tables
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

# Sign up function
def signup(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("Signup successful! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different one.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

# Login function
def login(username, password):
    user_query = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return user_query.fetchone()

# Add train to database
def add_train_destination(train_name, train_number, start_destination, end_destination):
    try:
        if not all([train_name, train_number, start_destination, end_destination]):
            st.error("All fields must be filled out.")
            return
        c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)",
                  (train_number, train_name, start_destination, end_destination))
        conn.commit()
        st.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")
    except sqlite3.Error as e:
        st.error(f"SQLite error while adding train: {e}")

# Book tickets
def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    try:
        # For simplicity, just display that the ticket is booked (you can extend this as needed)
        st.success(f"Ticket booked for {passenger_name} ({passenger_gender}, {passenger_age}) on train {train_number}. Seat type: {seat_type}.")
    except sqlite3.Error as e:
        st.error(f"SQLite error while booking tickets: {e}")

# Search for a train
def search_train(train_number):
    try:
        c.execute("SELECT * FROM trains WHERE train_no=?", (train_number,))
        train = c.fetchone()
        if train:
            st.success(f"Train found: {train}")
        else:
            st.warning("Train not found.")
    except sqlite3.Error as e:
        st.error(f"SQLite error while searching train: {e}")

# Main app function
def main():
    create_db()  # Create the database and tables if they don't exist

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    st.title("Railway Booking Management System")

    # Conditional login/signup flow
    if not st.session_state.logged_in:
        page = st.sidebar.radio("Select Page", ["Login", "Create Account"])

        if page == "Login":
            st.subheader("Login")
            login_username = st.text_input("Username", key='login_username')
            login_password = st.text_input("Password", type="password", key='login_password')

            if st.button("Login"):
                user = login(login_username, login_password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username  # Store username
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid username or password.")
        
        elif page == "Create Account":
            st.subheader("Create Account")
            signup_username = st.text_input("New Username", key='signup_username')
            signup_password = st.text_input("New Password", type="password", key='signup_password')

            if st.button("Create Account"):
                if signup_username and signup_password:
                    signup(signup_username, signup_password)
                else:
                    st.error("Please enter both username and password.")
    
    else:
        # If logged in, show operation options
        operation = st.selectbox("Select Operation", ["Add Train Destination", "Book Tickets", "Search Train"])

        if operation == "Add Train Destination":
            st.subheader("Add New Train")
            train_name = st.text_input("Train Name")
            train_number = st.text_input("Train Number")
            start_destination = st.text_input("Start Destination")
            end_destination = st.text_input("End Destination")

            if st.button("Add Train"):
                add_train_destination(train_name, train_number, start_destination, end_destination)

        elif operation == "Book Tickets":
            st.subheader("Book Tickets")
            train_number = st.text_input("Train Number")
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.text_input("Passenger Age")
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.selectbox("Seat Type", ["Window", "Aisle", "Middle"])

            if st.button("Book Ticket"):
                book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif operation == "Search Train":
            st.subheader("Search for a Train")
            train_number = st.text_input("Enter Train Number")

            if st.button("Search Train"):
                search_train(train_number)

# Run the app
if __name__ == "__main__":
    main()

# Close database connection at the end
conn.close()
