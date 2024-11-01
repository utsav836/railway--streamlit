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

# Function to add a new train destination
def add_train_destination(train_name, train_number, start_destination, end_destination):
    c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", 
              (train_number, train_name, start_destination, end_destination))
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
            st.write("Seat Number | Seat Type | Booked | Passenger Name | Passenger Age | Passenger Gender")
            for row in result:
                st.write(row)
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

# Function to book tickets for a train
def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    seat_number = allocate_seat(train_number, seat_type)
    if seat_number:
        c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", 
                  (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success("Ticket booked successfully.")
    else:
        st.warning("No available seats of this type.")

# Function to allocate a seat for booking
def allocate_seat(train_number, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
    result = seat_query.fetchone()
    return result[0] if result else None

# Function to search for a train
def search_train(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_no=?", (train_number,))
    return train_query.fetchone()

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

# Main function to handle Streamlit interface and operations
def main():
    st.title("Railway Management System")

    # Login/Signup Section
    if 'logged_in' not in st.session_state:
        st.subheader("Login or Signup")

        login_username = st.text_input("Username", key='login_username')
        login_password = st.text_input("Password", type="password", key='login_password')

        if st.button("Login"):
            user = login(login_username, login_password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password.")

        if st.button("Signup"):
            signup_username = st.text_input("New Username", key='signup_username')
            signup_password = st.text_input("New Password", type="password", key='signup_password')
            if st.button("Create Account"):
                signup(signup_username, signup_password)

    if st.session_state.get('logged_in'):
        st.success(f"Welcome, {st.session_state.username}!")
        operation = st.selectbox("Select Operation", ["Add Train Destination", "View Seats", "Book Tickets", "Search Train"])

        if operation == "Add Train Destination":
            train_name = st.text_input("Train Name")
            train_number = st.text_input("Train Number")
            start_destination = st.text_input("Start Destination")
            end_destination = st.text_input("End Destination")

            if st.button("Add Train"):
                add_train_destination(train_name, train_number, start_destination, end_destination)
                st.success(f"Train added: {train_name} ({train_number})")

        elif operation == "View Seats":
            train_number = st.text_input("Enter Train Number to View Seats")
            if st.button("View Seats"):
                view_seat(train_number)

        elif operation == "Book Tickets":
            train_number = st.text_input("Enter Train Number to Book Tickets")
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.text_input("Passenger Age")
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.selectbox("Seat Type", ["window", "aisle", "middle"])

            if st.button("Book Ticket"):
                book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

        elif operation == "Search Train":
            train_number = st.text_input("Enter Train Number to Search")
            if st.button("Search Train"):
                train_data = search_train(train_number)
                if train_data:
                    st.success(f"Train found: {train_data}")
                else:
                    st.warning("Train not found.")

    conn.close()

if __name__ == "__main__":
    create_db()  # Create database and tables if they don't exist
    main()
