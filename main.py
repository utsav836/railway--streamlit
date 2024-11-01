import streamlit as st
import sqlite3
from google.oauth2 import id_token
from google.auth.transport import requests
import os

# SQLite database connection
conn = sqlite3.connect('railwaydb', check_same_thread=False)
c = conn.cursor()

# Function to create initial database tables if they don't exist
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

# Function to add a new user
def add_user(username, password):
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

# Function to check if a user exists
def check_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

# Function to verify Google token
def verify_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID"))
        return idinfo['email']
    except ValueError:
        return None

# Function to add a new train destination
def add_train_destination(train_name, train_number, start_destination, end_destination):
    c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_number, train_name, start_destination, end_destination))
    conn.commit()
    create_seat_table(train_number)

# Function to create a seat table for a train
def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)

# Function to insert seats into a train's seat table
def insert_seats(train_number):
    for i in range(1, 201):  # Assuming there are 200 seats per train
        val = categorize_seat(i)
        parameters = (i, val, 0, '', '', '')
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
    conn.commit()

# Function to categorize seat type based on seat number
def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

# Function to view seat details for a train
def view_seat(train_number):
    try:
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        
        if result:
            st.write("### Seat Details")
            for row in result:
                seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender = row
                booked_status = "Yes" if booked else "No"
                st.write(f"**Seat Number:** {seat_number}, **Seat Type:** {seat_type}, **Booked:** {booked_status}, **Passenger Name:** {passenger_name}, **Passenger Age:** {passenger_age}, **Passenger Gender:** {passenger_gender}")
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

# Function to book tickets for a train
def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    try:
        seat_number = allocate_seat(train_number, seat_type)
        if seat_number:
            c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (passenger_name, passenger_age, passenger_gender, seat_number))
            conn.commit()
            st.success("Ticket booked successfully.")
        else:
            st.warning("No available seats of this type.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

# Function to allocate a seat for booking
def allocate_seat(train_number, seat_type):
    try:
        seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = seat_query.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

# Function to search for a train based on train number
def search_train(train_number):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=?", (train_number,))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

# Main function to handle Streamlit interface and operations
def main():
    st.title("Railway Management System")
    
    # Check if user is logged in
    if 'logged_in' not in st.session_state:
        # Login and Signup Section
        st.sidebar.header("User Authentication")
        option = st.sidebar.selectbox("Select Option", ["Login", "Signup", "Google Sign-In"])
        
        if option == "Login":
            username = st.sidebar.text_input("Username")
            password = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login"):
                if check_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                else:
                    st.error("Invalid username or password.")

        elif option == "Signup":
            new_username = st.sidebar.text_input("New Username")
            new_password = st.sidebar.text_input("New Password", type="password")
            if st.sidebar.button("Signup"):
                try:
                    add_user(new_username, new_password)
                    st.success("Signup successful! You can now log in.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different username.")

        elif option == "Google Sign-In":
            token = st.sidebar.text_input("Enter Google Token")
            if st.sidebar.button("Sign in with Google"):
                email = verify_google_token(token)
                if email:
                    st.session_state.logged_in = True
                    st.session_state.username = email
                    st.success("Google Sign-In successful!")
                else:
                    st.error("Invalid Google token.")

    else:
        st.sidebar.success("Logged in as: " + st.session_state.username)
        operation = st.sidebar.selectbox("Select Operation", ["Create Database", "Add Train Destination", "View Seats", "Book Tickets", "Search Train"])

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
                st.sidebar.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")

        elif operation == "View Seats":
            train_number = st.sidebar.text_input("Enter Train Number to View Seats")
            if st.sidebar.button("View Seats"):
                view_seat(train_number)

        elif operation == "Book Tickets":
            train_number = st.sidebar.text_input("Enter Train Number to Book Tickets")
            passenger_name = st.sidebar.text_input("Passenger Name")
            passenger_age = st.sidebar.text_input("Passenger Age")
            passenger_gender = st.sidebar.selectbox("Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.sidebar.selectbox("Seat Type", ["window", "aisle", "middle"])

            if st.sidebar.button("Book Ticket"):
                book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif operation == "Search Train":
            train_number = st.sidebar.text_input("Enter Train Number to Search")
            if st.sidebar.button("Search Train"):
                train_data = search_train(train_number)
                if train_data:
                    st.sidebar.success(f"Train found: {train_data}")
                else:
                    st.sidebar.warning(f"Train {train_number} not found.")

    conn.close()

if __name__ == "__main__":
    main()
