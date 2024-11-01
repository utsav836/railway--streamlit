import streamlit as st
import pandas as pd
import sqlite3

conn = sqlite3.connect('railwaydb.db', check_same_thread=False)
c = conn.cursor()

def create_db():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT)")
        conn.commit()
        st.success("Database created successfully.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

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
        c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
        conn.commit()
        insert_seats(train_number)
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def insert_seats(train_number):
    try:
        for i in range(1, 201):
            val = categorize_seat(i)
            parameters = (i, val, 0, '', '', '')
            c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
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
    try:
        seat_query = c.execute(f"SELECT seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender FROM seats_{train_number} ORDER BY seat_number ASC")
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
        train_data = search_train(train_number)
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(f"Train {train_number} and associated seats have been canceled successfully.")
        else:
            st.warning(f"Train {train_number} not found.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def delete_train(train_number):
    try:
        train_data = search_train(train_number)
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(f"Train {train_number} and associated seats have been deleted successfully.")
        else:
            st.warning(f"Train {train_number} not found.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def search_train(train_number):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=?", (train_number,))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

def allocate_seat_manual(train_number, seat_number, passenger_name, passenger_age, passenger_gender):
    try:
        c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", 
                  (passenger_name, passenger_age, passenger_gender, seat_number))
        conn.commit()
        st.success("Seat allocated successfully.")
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")

def get_chatbot_response(user_input):
    responses = {
        "train schedule": "I can help with the train schedule. Please provide the train number.",
        "book ticket": "To book a ticket, please provide your name, age, gender, and the train number.",
        "cancel ticket": "To cancel a ticket, please provide the booking details.",
        "train number": "Please provide the train number to get more details.",
        "default": "Sorry, I didn't understand that. Can you please provide more details?"
    }
    return responses.get(user_input.lower(), responses["default"])

def main():
    st.title("Railway Management System")
    
    operation = st.selectbox(
        "Choose Operation",
        [
            "Create Database",
            "Add Train",
            "Cancel Train",
            "Delete Train",
            "View Seats",
            "Book Tickets",
            "Search Train",
            "Allocate Seat",
            "Chat with Bot"
        ]
    )
    
    if operation == "Create Database":
        create_db()
    
    elif operation == "Add Train":
        with st.form(key='add_train_form'):
            train_name = st.text_input("Train Name", key='train_name')
            train_number = st.text_input("Train Number", key='train_number')
            submit_button = st.form_submit_button(label="Add Train")

            if submit_button:
                add_train(train_name, train_number)
    
    elif operation == "Cancel Train":
        with st.form(key='cancel_train_form'):
            train_number = st.text_input("Train Number", key='cancel_train_number')
            submit_button = st.form_submit_button(label="Cancel Train")

            if submit_button:
                cancel_train(train_number)
    
    elif operation == "Delete Train":
        with st.form(key='delete_train_form'):
            train_number = st.text_input("Train Number", key='delete_train_number')
            submit_button = st.form_submit_button(label="Delete Train")

            if submit_button:
                delete_train(train_number)
    
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
            train_name = st.text_input("Train Name (optional)", key='search_train_name')
            submit_button = st.form_submit_button(label="Search Train")

            if submit_button:
                train_data = search_train(train_number)
                if train_data:
                    st.success(f"Train found: {train_data}")
                else:
                    st.warning(f"Train {train_number} with name '{train_name}' not found.")
    
    elif operation == "Allocate Seat":
        with st.form(key='seat_allocation_form'):
            train_number = st.text_input("Train Number", key='allocation_train_number')
            seat_number = st.text_input("Seat Number", key='seat_number')
            passenger_name = st.text_input("Passenger Name", key='allocation_passenger_name')
            passenger_age = st.text_input("Passenger Age", key='allocation_passenger_age')
            passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"], key='allocation_passenger_gender')
            submit_button = st.form_submit_button(label="Allocate Seat")

            if submit_button:
                allocate_seat_manual(train_number, seat_number, passenger_name, passenger_age, passenger_gender)
    
    elif operation == "Chat with Bot":
        st.header("Chat with Bot")
        user_input = st.text_input("Ask me anything about the railway system:")
        if user_input:
            response = get_chatbot_response(user_input)
            st.write(response)

if __name__ == "__main__":
    main()
