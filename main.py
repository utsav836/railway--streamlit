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

# Functions for train management
def add_train(train_name, train_number, start_destination, end_destination):
    try:
        c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_number, train_name, start_destination, end_destination))
        create_seat_table(train_number)
        conn.commit()
        st.success("Train added successfully.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def create_seat_table(train_number):
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS seats_{train_number} (
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

def insert_seats(train_number):
    for i in range(1, 201):  # Assuming there are 200 seats per train
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

def view_seat(train_number):
    try:
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        if result:
            st.write("Seat Availability:")
            for row in result:
                booked_status = "Booked" if row[2] == 1 else "Available"
                st.write(f"Seat {row[0]} ({row[1]}): {booked_status} - Passenger: {row[3] if row[2] == 1 else 'N/A'}")
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    seat_number = allocate_seat(train_number, seat_type)
    if seat_number:
        c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success("Ticket booked successfully.")
    else:
        st.warning("No available seats of this type.")

def allocate_seat(train_number, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
    result = seat_query.fetchone()
    return result[0] if result else None

# Main function to handle Streamlit interface
def main():
    create_db()  # Create database and tables if they don't exist

    st.title("Railway Management System")

    # Login Section
    st.subheader("Login")
    login_username = st.text_input("Username", key='login_username')
    login_password = st.text_input("Password", type="password", key='login_password')

    if st.button("Login"):
        user = login(login_username, login_password)
        if user:
            st.success("Logged in successfully!")
            st.write(f"Welcome, {login_username}!")

            # Train management features
            operation = st.selectbox("Select Operation", ["Add Train", "View Seats", "Book Tickets", "View Trains"])

            if operation == "Add Train":
                train_name = st.text_input("Train Name")
                train_number = st.text_input("Train Number")
                start_destination = st.text_input("Start Destination")
                end_destination = st.text_input("End Destination")

                if st.button("Add Train"):
                    if train_name and train_number and start_destination and end_destination:
                        add_train(train_name, train_number, start_destination, end_destination)
                    else:
                        st.error("Please fill in all fields.")

            elif operation == "View Seats":
                train_number = st.text_input("Enter Train Number to View Seats")
                if st.button("View Seats"):
                    if train_number:
                        view_seat(train_number)
                    else:
                        st.error("Please enter a train number.")

            elif operation == "Book Tickets":
                train_number = st.text_input("Enter Train Number to Book Tickets")
                passenger_name = st.text_input("Passenger Name")
                passenger_age = st.text_input("Passenger Age")
                passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
                seat_type = st.selectbox("Seat Type", ["window", "aisle", "middle"])

                if st.button("Book Ticket"):
                    if train_number and passenger_name and passenger_age:
                        book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)
                    else:
                        st.error("Please fill in all fields.")

            elif operation == "View Trains":
                trains = view_trains()
                if trains:
                    st.write("Trains in the system:")
                    for train in trains:
                        st.write(f"Train No: {train[0]}, Name: {train[1]}, From: {train[2]}, To: {train[3]}")
                else:
                    st.info("No trains found.")

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

if __name__ == "__main__":
    main()
