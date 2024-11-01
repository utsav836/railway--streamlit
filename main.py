import streamlit as st
import sqlite3

# Establish connection to SQLite database
conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

# Function to create initial database tables if they don't exist
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

# User authentication functions
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

# Train management functions
def add_train(train_name, train_number, start_destination, end_destination):
    try:
        c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_number, train_name, start_destination, end_destination))
        conn.commit()
        create_seat_table(train_number)
        st.success("Train added successfully.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)

def insert_seats(train_number):
    for i in range(1, 201):  # Assuming 200 seats per train
        seat_type = categorize_seat(i)
        parameters = (i, seat_type, 0, '', '', '')
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
    conn.commit()

def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

def view_trains():
    trains = c.execute("SELECT * FROM trains").fetchall()
    if trains:
        for train in trains:
            st.write(f"Train No: {train[0]}, Name: {train[1]}, From: {train[2]}, To: {train[3]}")
    else:
        st.info("No trains found.")

def view_seat(train_number):
    try:
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        if result:
            for seat in result:
                status = "Booked" if seat[2] else "Available"
                st.write(f"Seat {seat[0]} ({seat[1]}): {status} | Passenger: {seat[3]}, Age: {seat[4]}, Gender: {seat[5]}")
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

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

def allocate_seat(train_number, seat_type):
    try:
        seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = seat_query.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

def main():
    create_db()  # Create database and tables if they don't exist

    # Check if user is logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    st.title("Railway Management System")

    if not st.session_state.logged_in:
        # Login Section
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

        # Signup Section
        st.subheader("Create Account")
        signup_username = st.text_input("New Username", key='signup_username')
        signup_password = st.text_input("New Password", type="password", key='signup_password')

        if st.button("Create Account"):
            if signup_username and signup_password:
                signup(signup_username, signup_password)
            else:
                st.error("Please enter both username and password.")
    else:
        # Main App Logic after Login
        st.sidebar.title("Operations")
        operation = st.sidebar.selectbox("Choose an operation", ["Add Train", "View Trains", "Book Tickets", "View Seats"])

        if operation == "Add Train":
            st.subheader("Add a New Train")
            with st.form(key='add_train_form'):
                train_name = st.text_input("Train Name", key='train_name')
                train_number = st.text_input("Train Number", key='train_number')
                start_destination = st.text_input("Start Destination", key='start_destination')
                end_destination = st.text_input("End Destination", key='end_destination')
                submit_button = st.form_submit_button(label="Add Train")
                
                if submit_button:
                    add_train(train_name, train_number, start_destination, end_destination)

        elif operation == "View Trains":
            st.subheader("Available Trains")
            view_trains()

        elif operation == "Book Tickets":
            st.subheader("Book Tickets")
            train_number = st.text_input("Enter Train Number")
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.text_input("Passenger Age")
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.selectbox("Seat Type", ["window", "aisle", "middle"])

            if st.button("Book Ticket"):
                book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif operation == "View Seats":
            st.subheader("View Seats for a Train")
            train_number = st.text_input("Enter Train Number to View Seats")
            if st.button("View Seats"):
                view_seat(train_number)

    conn.close()

if __name__ == "__main__":
    main()
