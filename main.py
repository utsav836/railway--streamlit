import streamlit as st
import sqlite3

# Establish database connection
conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

def signup(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("Signup successful! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different one.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def login(username, password):
    user_query = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return user_query.fetchone()

def add_train_destination(train_name, train_number, start_destination, end_destination):
    try:
        # Debugging: Ensure that all values are being passed correctly
        st.write(f"Adding train with details: {train_name}, {train_number}, {start_destination}, {end_destination}")

        # Ensure that inputs are not empty
        if not all([train_name, train_number, start_destination, end_destination]):
            st.error("All fields must be filled out.")
            return
        
        # Insert train details into database
        c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", 
                  (train_number, train_name, start_destination, end_destination))
        conn.commit()
        
        # Create seat table for the train
        create_seat_table(train_number)
        st.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")

    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def create_seat_table(train_number):
    try:
        c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
        conn.commit()
        insert_seats(train_number)
    except sqlite3.Error as e:
        st.error(f"Error creating seat table: {e}")

def insert_seats(train_number):
    try:
        for i in range(1, 201):  # Assuming there are 200 seats per train
            val = categorize_seat(i)
            parameters = (i, val, 0, '', '', '')
            c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error inserting seats: {e}")

def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

# The rest of your app continues here...
# (including login, signup, view_seat, book_tickets, etc.)

def main():
    create_db()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    st.title("Railway Booking Management System")

    # Conditional navigation
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
        st.sidebar.title("Operations")
        operation = st.sidebar.selectbox("Select Operation", ["Create Database", "Add Train Destination", "Cancel Train", "Delete Train", "View Seats", "Book Tickets", "Search Train"])

        if operation == "Create Database":
            create_db()
            st.sidebar.success("Database created successfully.")

        elif operation == "Add Train Destination":
            train_name = st.sidebar.text_input("Train Name")
            train_number = st.sidebar.text_input("Train Number")
            start_destination = st.sidebar.text_input("Start Destination")
            end_destination = st.sidebar.text_input("End Destination")

            if st.sidebar.button("Add Train"):
                add_train_destination(train_name, train_number, start_destination, end_destination)

        # Handle other operations (Cancel Train, Delete Train, View Seats, etc.)

    conn.close()

if __name__ == "__main__":
    main()
