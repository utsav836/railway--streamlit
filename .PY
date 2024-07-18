import streamlit as st
import sqlite3
import pandas as pd
import speech_recognition as sr  # Importing Speech Recognition library

# Establish SQLite connection
conn = sqlite3.connect('railwaydb')
c = conn.cursor()

# Function to create database tables if they do not exist
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

# Function to create seat table for a train
def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
    conn.commit()
    insert_seats(train_number)

# Function to insert seats into a seat table
def insert_seats(train_number):
    for i in range(1, 201):  # Assuming there are 200 seats per train
        val = categorize_seat(i)
        parameters = (i, val, 0, '', '', '')
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
    conn.commit()

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

# Function to book tickets for a given train
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

# Function to search for a train by train number and optional train name
def search_train(train_number, train_name):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return None

# Function for speech recognition
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Speak now...")
        audio = r.listen(source)

    try:
        spoken_text = r.recognize_google(audio)
        return spoken_text.lower()
    except sr.UnknownValueError:
        st.warning("Could not understand audio.")
        return None
    except sr.RequestError:
        st.error("Speech recognition service unavailable.")
        return None

# Main function to run the Streamlit app
def main():
    st.info("Click the button or speak 'English' or 'Hindi'")
    spoken_language = recognize_speech()
    if spoken_language:
        if "english" in spoken_language:
            language = "English"
        elif "hindi" in spoken_language or "हिंदी" in spoken_language:
            language = "हिन्दी"
        else:
            st.warning("Unsupported language. Defaulting to English.")
            language = "English"
    else:
        language = "English"

    if language == "English":
        st.title("Railway Management System")
        st.header("Options")
        options = [
            "Create Database", "Add Train Destination", "Cancel Train", 
            "Delete Train", "View Seats", "Book Tickets", "Search Train"
        ]
    elif language == "हिन्दी":
        st.title("रेलवे प्रबंधन प्रणाली")
        st.header("विकल्प")
        options = [
            "डेटाबेस बनाएं", "ट्रेन डेस्टिनेशन जोड़ें", "ट्रेन रद्द करें", 
            "ट्रेन हटाएं", "सीटें देखें", "टिकट बुक करें", "ट्रेन खोजें"
        ]

    # Display options centered in the layout
    with st.container():
        for option in options:
            st.button(option, key=option)

# Run the main function when the script is executed
if __name__ == "__main__":
    create_db()  # Ensure database is created on script start
    main()

# Close the SQLite connection after operations are done
conn.close()
