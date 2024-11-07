import streamlit as st
import sqlite3


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
    c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_number, train_name, start_destination, end_destination))
    conn.commit()
    create_seat_table(train_number)
    
def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)

def insert_seats(train_number):
    for i in range(1, 201):  # Assuming there are 200 seats per train
        val = categorize_seat(i)
        parameters = (i, val, 0, '', '', '')
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
            st.dataframe(data=result)
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


def cancel_train(train_number):
    try:
        train_data = search_train(train_number, '')
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(f"Train {train_number} and associated seats have been canceled successfully.")
        else:
            st.warning(f"Train {train_number} does not exist.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def delete_train(train_number):
    try:
        train_data = search_train(train_number, '')
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(f"Train {train_number} and associated seats have been deleted successfully.")
        else:
            st.warning(f"Train {train_number} does not exist.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")


def search_train(train_number, train_name):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

def main():
    create_db()  

    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    st.title("Railway Booking Management System")

    if not st.session_state.logged_in:
    
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
            st.sidebar.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")

    elif operation == "Cancel Train":
        train_number = st.sidebar.text_input("Train Number to Cancel")

        if st.sidebar.button("Cancel Train"):
            cancel_train(train_number)

    elif operation == "Delete Train":
        train_number = st.sidebar.text_input("Train Number to Delete")

        if st.sidebar.button("Delete Train"):
            delete_train(train_number)

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
        train_name = st.sidebar.text_input("Enter Train Name (optional)")

        if st.sidebar.button("Search Train"):
            train_data = search_train(train_number, train_name)
            if train_data:
                st.sidebar.success(f"Train found: {train_data}")
            else:
                st.sidebar.warning(f"Train {train_number} with name '{train_name}' not found.")

    conn.close()



if __name__ == "__main__":
    main()
