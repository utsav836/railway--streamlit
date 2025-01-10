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
        create_seat_table(train_number)
        st.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")
    except sqlite3.Error as e:
        st.error(f"SQLite error while adding train: {e}")

# Create seats for the train in the database
def create_seat_table(train_number):
    try:
        c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
        conn.commit()
        insert_seats(train_number)
    except sqlite3.Error as e:
        st.error(f"Error creating seat table: {e}")

# Insert seat information into the database
def insert_seats(train_number):
    try:
        for i in range(1, 201):  # Assuming there are 200 seats per train
            seat_type = categorize_seat(i)
            c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type) VALUES (?, ?)", (i, seat_type))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error inserting seats: {e}")

# Categorize seat type based on seat number
def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

# Book tickets
def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    try:
        seat_number = allocate_seat(train_number, seat_type)
        if seat_number:
            c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?",
                      (passenger_name, passenger_age, passenger_gender, seat_number))
            conn.commit()
            st.success(f"Ticket booked for {passenger_name} on train {train_number}. Seat Number: {seat_number}, Seat Type: {seat_type}")
        else:
            st.warning("No available seats of this type.")
    except sqlite3.Error as e:
        st.error(f"SQLite error while booking tickets: {e}")

# Allocate a seat based on the seat type
def allocate_seat(train_number, seat_type):
    try:
        c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = c.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"SQLite error while allocating seat: {e}")
        return None

# View all seats for a specific train
def view_seat(train_number):
    try:
        c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = c.fetchall()
        if result:
            st.dataframe(result, columns=["Seat Number", "Seat Type", "Booked", "Passenger Name", "Passenger Age", "Passenger Gender"])
        else:
            st.info(f"No seats found for train {train_number}.")
    except sqlite3.Error as e:
        st.error(f"SQLite error while viewing seats: {e}")

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
        operation = st.selectbox("Select Operation", ["Add Train Destination", "Book Tickets", "View Seats", "Search Train"])

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

        elif operation == "View Seats":
            st.subheader("View All Seats")
            train_number = st.text_input("Enter Train Number")

            if st.button("View Seats"):
                view_seat(train_number)

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
