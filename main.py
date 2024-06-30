import streamlit as st
import sqlite3

conn = sqlite3.connect('railwaydb')
c = conn.cursor()

def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT, train_name TEXT, start_destination TEXT, end_destination TEXT)")
    conn.commit()

def search_train(train_number, train_name):
    train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
    train_data = train_query.fetchone()
    return train_data

def train_destination(start_destination, end_destination):
    train_query = c.execute("SELECT * FROM trains WHERE start_destination=? AND end_destination=?", (start_destination, end_destination))
    train_data = train_query.fetchone()
    return train_data

def add_train_destination(train_name, train_number, start_destination, end_destination):
    c.execute("INSERT INTO trains (train_name, train_no, start_destination, end_destination) VALUES (?, ?, ?, ?)", (train_name, train_number, start_destination, end_destination))
    conn.commit()
    create_seat_table(train_number)

def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)

def insert_seats(train_number):
    for i in range(1, 201):  # Adjusted range to include 200 seats
        val = categorize_seat(i)
        parameters = (i, val, 0, '', '', '')
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
    conn.commit()

def allocate_seat(train_number, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC", (seat_type,))
    result = seat_query.fetchone()
    return result[0] if result else None

def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

def view_seat(train_number):
    seat_query = c.execute(f"SELECT seat_number, seat_type, passenger_name, passenger_age, passenger_gender, booked FROM seats_{train_number} ORDER BY seat_number ASC")
    result = seat_query.fetchall()
    if result:
        st.dataframe(data=result)

def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    seat_number = allocate_seat(train_number, seat_type)
    if seat_number:
        c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success("BOOKED SUCCESSFULLY")

def cancel_train(train_number):
    train_data = search_train(train_number, '')
    if train_data:
        c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
        conn.commit()
        c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
        conn.commit()
        st.success(f"Train {train_number} and associated seats have been canceled successfully.")
    else:
        st.warning(f"Train {train_number} does not exist.")

def delete_train(train_number):
    train_data = search_train(train_number, '')
    if train_data:
        c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
        conn.commit()
        c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
        conn.commit()
        st.success(f"Train {train_number} and associated seats have been deleted successfully.")
    else:
        st.warning(f"Train {train_number} does not exist.")

def main():
    st.sidebar.title("Railway Management System")
    operation = st.sidebar.selectbox("Select Operation", ["Create Database", "Add Train Destination", "Cancel Train", "Delete Train"])

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

    conn.close()

if __name__ == "__main__":
    main()
