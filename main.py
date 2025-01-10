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

# Other functions for adding trains, booking tickets, etc. stay the same.

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
