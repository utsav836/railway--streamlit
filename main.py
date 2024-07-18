import streamlit as st
import sqlite3
import pandas as pd

# Function to create or connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('railwaydb')
    c = conn.cursor()
    return conn, c

# Function to create database tables if they do not exist
def create_db():
    conn, c = connect_db()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()
    conn.close()

# Function to add a new train destination
def add_train_destination(train_name, train_number, start_destination, end_destination):
    conn, c = connect_db()
    c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_number, train_name, start_destination, end_destination))
    conn.commit()
    create_seat_table(train_number)
    conn.close()

# Function to create seat table for a train
def create_seat_table(train_number):
    conn, c = connect_db()
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)
    conn.close()

# Function to insert seats into a seat table
def insert_seats(train_number):
    conn, c = connect_db()
    for i in range(1, 201):  # Assuming there are 200 seats per train
        val = categorize_seat(i)
        parameters = (i, val, 0, '', '', '')
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
    conn.commit()
    conn.close()

# Function to categorize seat types
def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

# Function to view seats for a given train
def view_seat(train_number):
    conn, c = connect_db()
    try:
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        if result:
            df = pd.DataFrame(result, columns=['Seat Number', 'Seat Type', 'Booked', 'Passenger Name', 'Passenger Age', 'Passenger Gender'])
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}))  # Center align DataFrame
        else:
            st.info("No seats found for this train.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
    conn.close()

# Function to book tickets for a given train
def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    conn, c = connect_db()
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
    conn.close()

# Function to allocate a seat for booking
def allocate_seat(train_number, seat_type):
    conn, c = connect_db()
    try:
        seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = seat_query.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None
    conn.close()

# Function to cancel a train and associated seats
def cancel_train(train_number):
    conn, c = connect_db()
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
    conn.close()

# Function to delete a train and associated seats
def delete_train(train_number):
    conn, c = connect_db()
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
    conn.close()

# Function to search for a train by train number and optional train name
def search_train(train_number, train_name):
    conn, c = connect_db()
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None
    conn.close()

# Main function to run the Streamlit app
def main():
    st.title("Railway Management System")
    st.markdown(
        """
        <style>
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar for operations
    st.sidebar.title("Operations")

    # Language selection
    language = st.sidebar.selectbox("Select Language / भाषा चुनें", ["English", "हिन्दी"])

    # Displaying operations in the center of the window
    if language == "English":
        operation = st.sidebar.selectbox("Select Operation", ["Create Database", "Add Train Destination", "Cancel Train", "Delete Train", "View Seats", "Book Tickets", "Search Train"])
    elif language == "हिन्दी":
        operation = st.sidebar.selectbox("ऑपरेशन चुनें", ["डेटाबेस बनाएं", "ट्रेन डेस्टिनेशन जोड़ें", "ट्रेन रद्द करें", "ट्रेन हटाएं", "सीटें देखें", "टिकट बुक करें", "ट्रेन खोजें"])

    if operation == "Create Database" or operation == "डेटाबेस बनाएं":
        create_db()
        st.sidebar.success("Database created successfully / डेटाबेस सफलतापूर्वक बनाया गया.")

    elif operation == "Add Train Destination" or operation == "ट्रेन डेस्टिनेशन जोड़ें":
        train_name = st.sidebar.text_input("Train Name / ट्रेन का नाम")
        train_number = st.sidebar.text_input("Train Number / ट्रेन नंबर")
        start_destination = st.sidebar.text_input("Start Destination / प्रारंभिक स्थान")
        end_destination = st.sidebar.text_input("End Destination / अंतिम स्थान")

        if st.sidebar.button("Add Train / ट्रेन जोड़ें"):
            add_train_destination(train_name, train_number, start_destination, end_destination)
            st.sidebar.success(f"Train added successfully / ट्रेन सफलतापूर्वक जोड़ी गई: {train_name}, Train Number / ट्रेन नंबर: {train_number}, From / से: {start_destination}, To / तक: {end_destination}")

    elif operation ==
