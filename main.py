import streamlit as st
import sqlite3

# Establish connection to SQLite database
conn = sqlite3.connect('railwaydb')
c = conn.cursor()

# Function to create initial database tables if they don't exist
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

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
        # Check if the train exists in the trains table
        train_exists = c.execute("SELECT 1 FROM trains WHERE train_no=?", (train_number,)).fetchone()
        if not train_exists:
            st.warning(f"Train {train_number} does not exist.")
            return
        
        # Check if the seats table for the given train exists
        table_exists = c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='seats_{train_number}'").fetchone()
        if not table_exists:
            st.warning(f"No seat data found for Train {train_number}.")
            return
        
        # Query for the seats in the train
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()
        
        if result:
            st.write("### Seat Details")
            st.dataframe(result)
        else:
            st.info("No seats available for this train.")
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

# Function to cancel a train and associated seats
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

# Function to delete a train and associated seats
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

# Function to search for a train based on train number and name
def search_train(train_number, train_name):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

# Main function to handle Streamlit interface and operations
def main():
    st.set_page_config(page_title="Railway Management System", layout="wide")

    # Centralized layout using columns
    col1, col2, col3 = st.columns([1, 3, 1])  # Creates three columns (for centering content)

    with col2:
        # Title in center
        st.markdown("# Railway Management System")
        operation = st.selectbox("Select Operation", ["Create Database", "Add Train Destination", "Cancel Train", "Delete Train", "View Seats", "Book Tickets", "Search Train"])

        if operation == "Create Database":
            create_db()
            st.success("Database created successfully.")

        elif operation == "Add Train Destination":
            train_name = st.text_input("Train Name")
            train_number = st.text_input("Train Number")
            start_destination = st.text_input("Start Destination")
            end_destination = st.text_input("End Destination")

            if st.button("Add Train"):
                add_train_destination(train_name, train_number, start_destination, end_destination)
                st.success(f"Train added successfully: {train_name}, Train Number: {train_number}, From: {start_destination}, To: {end_destination}")

        elif operation == "Cancel Train":
            train_number = st.text_input("Train Number to Cancel")

            if st.button("Cancel Train"):
                cancel_train(train_number)

        elif operation == "Delete Train":
            train_number = st.text_input("Train Number to Delete")

            if st.button("Delete Train"):
                delete_train(train_number)

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
            train_name = st.text_input("Enter Train Name (optional)")

            if st.button("Search Train"):
                train_data = search_train(train_number, train_name)
                if train_data:
                    st.success(f"Train found: {train_data}")
                else:
                    st.warning(f"Train {train_number} with name '{train_name}' not found.")

    conn.close()

if __name__ == "__main__":
    main()
