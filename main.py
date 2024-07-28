import streamlit as st
import sqlite3
import pandas as pd

# Initialize the SQLite connection
conn = sqlite3.connect('railwaydb', check_same_thread=False)
c = conn.cursor()

# Language dictionaries
texts = {
    "English": {
        "title": "Railway Management System",
        "operations": "Operations",
        "create_db": "Create Database",
        "add_train": "Add Train Destination",
        "cancel_train": "Cancel Train",
        "delete_train": "Delete Train",
        "view_seats": "View Seats",
        "book_tickets": "Book Tickets",
        "search_train": "Search Train",
        "train_added_success": "Train added successfully",
        "train_canceled_success": "Train {train_number} and associated seats have been canceled successfully.",
        "train_deleted_success": "Train {train_number} and associated seats have been deleted successfully.",
        "ticket_booked_success": "Ticket booked successfully.",
        "ticket_not_booked": "Failed to book ticket. Please try again.",
        "train_found": "Train found: {train_data}",
        "train_not_found": "Train {train_number} with name '{train_name}' not found.",
        "database_created": "Database created successfully",
        "no_seats_found": "No seats found for this train.",
        "no_available_seats": "No available seats of this type.",
        "sqlite_error": "SQLite error: {error}"
    },
    "हिन्दी": {
        "title": "रेलवे प्रबंधन प्रणाली",
        "operations": "कार्रवाई",
        "create_db": "डेटाबेस बनाएं",
        "add_train": "ट्रेन डेस्टिनेशन जोड़ें",
        "cancel_train": "ट्रेन रद्द करें",
        "delete_train": "ट्रेन हटाएं",
        "view_seats": "सीटें देखें",
        "book_tickets": "टिकट बुक करें",
        "search_train": "ट्रेन खोजें",
        "train_added_success": "ट्रेन सफलतापूर्वक जोड़ी गई",
        "train_canceled_success": "ट्रेन {train_number} और संबंधित सीटें सफलतापूर्वक रद्द कर दी गई हैं।",
        "train_deleted_success": "ट्रेन {train_number} और संबंधित सीटें सफलतापूर्वक हटा दी गई हैं।",
        "ticket_booked_success": "टिकट सफलतापूर्वक बुक किया गया।",
        "ticket_not_booked": "टिकट बुक करने में विफल। कृपया फिर से प्रयास करें।",
        "train_found": "ट्रेन मिली: {train_data}",
        "train_not_found": "ट्रेन {train_number} नाम '{train_name}' के साथ नहीं मिली।",
        "database_created": "डेटाबेस सफलतापूर्वक बनाया गया",
        "no_seats_found": "इस ट्रेन के लिए कोई सीटें नहीं मिलीं।",
        "no_available_seats": "इस प्रकार की कोई उपलब्ध सीटें नहीं हैं।",
        "sqlite_error": "SQLite त्रुटि: {error}"
    }
}

def create_db():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT PRIMARY KEY, train_name TEXT, start_destination TEXT, end_destination TEXT)")
        conn.commit()
        st.success(texts[st.session_state.language]["database_created"])
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def add_train_destination(train_name, train_number, start_destination, end_destination):
    try:
        c.execute("INSERT INTO trains (train_no, train_name, start_destination, end_destination) VALUES (?, ?, ?, ?)",
                  (train_number, train_name, start_destination, end_destination))
        conn.commit()
        create_seat_table(train_number)
        st.success(texts[st.session_state.language]["train_added_success"])
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def create_seat_table(train_number):
    try:
        c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} (seat_number INTEGER PRIMARY KEY, seat_type TEXT, booked INTEGER DEFAULT 0, passenger_name TEXT, passenger_age TEXT, passenger_gender TEXT)")
        conn.commit()
        insert_seats(train_number)
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def insert_seats(train_number):
    try:
        for i in range(1, 201):
            val = categorize_seat(i)
            parameters = (i, val, 0, '', '', '')
            c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)", parameters)
        conn.commit()
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

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
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}))  # Center align DataFrame
        else:
            st.info(texts[st.session_state.language]["no_seats_found"])
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    try:
        seat_number = allocate_seat(train_number, seat_type)
        if seat_number:
            c.execute(f"UPDATE seats_{train_number} SET booked=1, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (passenger_name, passenger_age, passenger_gender, seat_number))
            conn.commit()
            st.success(texts[st.session_state.language]["ticket_booked_success"])
        else:
            st.warning(texts[st.session_state.language]["no_available_seats"])
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def allocate_seat(train_number, seat_type):
    try:
        seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC LIMIT 1", (seat_type,))
        result = seat_query.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))
        return None

def cancel_train(train_number):
    try:
        train_data = search_train(train_number, '')
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(texts[st.session_state.language]["train_canceled_success"].format(train_number=train_number))
        else:
            st.warning(texts[st.session_state.language]["train_not_found"].format(train_number=train_number, train_name=''))
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def delete_train(train_number):
    try:
        train_data = search_train(train_number, '')
        if train_data:
            c.execute("DELETE FROM trains WHERE train_no=?", (train_number,))
            conn.commit()
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            conn.commit()
            st.success(texts[st.session_state.language]["train_deleted_success"].format(train_number=train_number))
        else:
            st.warning(texts[st.session_state.language]["train_not_found"].format(train_number=train_number, train_name=''))
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))

def search_train(train_number, train_name):
    try:
        train_query = c.execute("SELECT * FROM trains WHERE train_no=? AND train_name=?", (train_number, train_name))
        train_data = train_query.fetchone()
        return train_data
    except sqlite3.Error as e:
        st.error(texts[st.session_state.language]["sqlite_error"].format(error=e))
        return None

def main():
    if 'language' not in st.session_state:
        st.title("Select Language / भाषा चुनें")
        lang = st.selectbox("Choose Language / भाषा चुनें", ["English", "हिन्दी"])
        if st.button("Submit"):
            st.session_state.language = lang
            st.experimental_rerun()
    else:
        st.title(texts[st.session_state.language]["title"])
        st.markdown(f'<div style="text-align: center; font-size: 24px;">{texts[st.session_state.language]["operations"]}</div>', unsafe_allow_html=True)
        
        # Operations selection
        operation = st.selectbox(
            texts[st.session_state.language]["operations"],
            [
                texts[st.session_state.language]["create_db"],
                texts[st.session_state.language]["add_train"],
                texts[st.session_state.language]["cancel_train"],
                texts[st.session_state.language]["delete_train"],
                texts[st.session_state.language]["view_seats"],
                texts[st.session_state.language]["book_tickets"],
                texts[st.session_state.language]["search_train"]
            ]
        )
        
        if operation == texts[st.session_state.language]["create_db"]:
            create_db()
        
        elif operation == texts[st.session_state.language]["add_train"]:
            with st.form(key='add_train_form'):
                train_name = st.text_input("Train Name / ट्रेन का नाम", key='train_name')
                train_number = st.text_input("Train Number / ट्रेन नंबर", key='train_number')
                start_destination = st.text_input("Start Destination / प्रारंभिक स्थान", key='start_destination')
                end_destination = st.text_input("End Destination / अंतिम स्थान", key='end_destination')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["add_train"])

                if submit_button:
                    add_train_destination(train_name, train_number, start_destination, end_destination)
        
        elif operation == texts[st.session_state.language]["cancel_train"]:
            with st.form(key='cancel_train_form'):
                train_number = st.text_input("Train Number to Cancel / रद्द करने के लिए ट्रेन नंबर", key='cancel_train_number')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["cancel_train"])

                if submit_button:
                    cancel_train(train_number)
        
        elif operation == texts[st.session_state.language]["delete_train"]:
            with st.form(key='delete_train_form'):
                train_number = st.text_input("Train Number to Delete / हटाने के लिए ट्रेन नंबर", key='delete_train_number')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["delete_train"])

                if submit_button:
                    delete_train(train_number)
        
        elif operation == texts[st.session_state.language]["view_seats"]:
            with st.form(key='view_seats_form'):
                train_number = st.text_input("Enter Train Number to View Seats / सीटें देखने के लिए ट्रेन नंबर दर्ज करें", key='view_seat_number')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["view_seats"])

                if submit_button:
                    view_seat(train_number)
        
        elif operation == texts[st.session_state.language]["book_tickets"]:
            with st.form(key='book_tickets_form'):
                train_number = st.text_input("Enter Train Number to Book Tickets / टिकट बुक करने के लिए ट्रेन नंबर दर्ज करें", key='book_ticket_number')
                passenger_name = st.text_input("Passenger Name / यात्री का नाम", key='passenger_name')
                passenger_age = st.text_input("Passenger Age / यात्री की आयु", key='passenger_age')
                passenger_gender = st.selectbox("Passenger Gender / यात्री का लिंग", ["Male / पुरुष", "Female / महिला", "Other / अन्य"], key='passenger_gender')
                seat_type = st.selectbox("Seat Type / सीट का प्रकार", ["window / खिड़की", "aisle / गलियारा", "middle / मध्य"], key='seat_type')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["book_tickets"])

                if submit_button:
                    book_tickets(train_number, passenger_name, passenger_age, passenger_gender, seat_type)
        
        elif operation == texts[st.session_state.language]["search_train"]:
            with st.form(key='search_train_form'):
                train_number = st.text_input("Enter Train Number to Search / खोज के लिए ट्रेन नंबर दर्ज करें", key='search_train_number')
                train_name = st.text_input("Enter Train Name (optional) / ट्रेन का नाम दर्ज करें (ऐच्छिक)", key='search_train_name')
                submit_button = st.form_submit_button(label=texts[st.session_state.language]["search_train"])

                if submit_button:
                    train_data = search_train(train_number, train_name)
                    if train_data:
                        st.success(texts[st.session_state.language]["train_found"].format(train_data=train_data))
                    else:
                        st.warning(texts[st.session_state.language]["train_not_found"].format(train_number=train_number, train_name=train_name))

if __name__ == "__main__":
    main()
