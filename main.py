import streamlit as st
import pandas as pd
import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

# Create necessary databases
def create_user_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    conn.commit()

def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT)")
    conn.commit()

create_user_db()
create_db()

# Hardcoded user credentials for demo purposes
users = {"admin": "password123"}

# User authentication function
def login(username, password):
    return username in users and users[username] == password

# Set a background image
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url('https://your-image-url.jpg'); /* Replace with your image URL */
            background-size: cover;
            background-position: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Functions for train management
def add_train(train_name, train_number):
    try:
        c.execute("INSERT INTO trains (train_no, train_name) VALUES (?, ?)", (train_number, train_name))
        conn.commit()
        create_seat_table(train_number)
        st.success("Train added successfully.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def create_seat_table(train_number):
    try:
        table_name = f"seats_{train_number}"
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                seat_number INTEGER PRIMARY KEY,
                seat_type TEXT,
                booked INTEGER DEFAULT 0,
                passenger_name TEXT,
                passenger_age TEXT,
                passenger_gender TEXT
            )
        """)
        conn.commit()
        insert_seats(train_number)
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def insert_seats(train_number):
    try:
        table_name = f"seats_{train_number}"
        for i in range(1, 201):
            seat_type = categorize_seat(i)
            parameters = (i, seat_type, 0, '', '', '')
            c.execute(f"INSERT INTO {table_name} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

def view_seat(train_number):
    table_name = f"seats_{train_number}"
    try:
        # Check if the table exists
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if c.fetchone() is None:
            st.error(f"No seat information found for train number {train_number}. Please ensure the train is added correctly.")
            return

        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM {table_name} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        if result:
            df = pd.DataFrame(result, columns=['Seat Number', 'Seat Type', 'Booked', 'Passenger Name', 'Passenger Age', 'Passenger Gender'])
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}))
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    try:
        seat_number = allocate_seat(train_number, seat_type)
        if seat_number:
            table_name = f"seats_{train_number}"
            c.execute(f"UPDATE {table_name} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (passenger_name, passenger_age, passenger_gender, seat_number))
            conn.commit()
            st.success("Ticket booked successfully.")
        else:
            st.warning("No available seats of this type.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def allocate_seat(train_number, seat_type):
    try:
        table_name = f"seats_{train_number}"
        seat_query = c.execute(f"SELECT seat_number FROM {table_name} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = seat_query.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

def search_train(train_number):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=?", (train_number,))
        return train_query.fetchone()
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

# Main app function
def main():
    set_background()
    st.title("Railway Management System")

    # Login section
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.subheader("Log In")
        with st.form(key='login_form'):
            username = st.text_input("Username", key='username')
            password = st.text_input("Password", type="password", key='password')
            submit_button = st.form_submit_button(label="Log In")

            if submit_button:
                if login(username, password):
                    st.session_state.logged_in = True
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid credentials.")
    else:
        st.success("Welcome back!")

        operation = st.selectbox(
            "Choose Operation",
            [
                "Add Train",
                "View Seats",
                "Book Tickets",
                "Search Train"
            ]
        )

        if operation == "Add Train":
            with st.form(key='add_train_form'):
                train_name = st.text_input("Train Name", key='train_name')
                train_number = st.text_input("Train Number", key='train_number')
                submit_button = st.form_submit_button(label="Add Train")

                if submit_button:
                    add_train(train_name, train_number)
        
        elif operation == "View Seats":
            with st.form(key='view_seats_form'):
                train_number = st.text_input("Train Number", key='view_seat_number')
                submit_button = st.form_submit_button(label="View Seats")

                if submit_button:
                    view_seat(train_number)

        elif operation == "Book Tickets":
            with st.form(key='book_tickets_form'):
                train_number = st.text_input("Train Number", key='book_ticket_number')
                passenger_name = st.text_input("Passenger Name", key='passenger_name')
                passenger_age = st.text_input("Passenger Age", key='passenger_age')
                passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"], key='passenger_gender')
                seat_type = st.selectbox("Seat Type", ["window", "aisle", "middle"], key='seat_type')
                submit_button = st.form_submit_button(label="Book Tickets")

                if submit_button:
                    book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif operation == "Search Train":
            with st.form(key='search_train_form'):
                train_number = st.text_input("Train Number", key='search_train_number')
                submit_button = st.form_submit_button(label="Search Train")

                if submit_button:
                    train_data = search_train(train_number)
                    if train_data:
                        st.success(f"Train found: {train_data}")
                    else:
                        st.warning(f"Train {train_number} not found.")

if __name__ == "__main__":
    main()
