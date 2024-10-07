
import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import datetime
import pytz
import psycopg2  # For PostgreSQL connection

dash.register_page(__name__, path="/test")

# Define the timezone (UTC+7)
tz_utc_7 = pytz.timezone('Asia/Bangkok')

# Helper function to generate time options in 15-minute increments
def generate_time_options(start_time="07:00", end_time="18:00", increment=15):
    time_format = "%H:%M"
    start = datetime.datetime.strptime(start_time, time_format)
    end = datetime.datetime.strptime(end_time, time_format)
    
    # Generate the list of time slots
    time_options = []
    while start <= end:
        time_str = start.strftime(time_format)
        time_options.append({"label": time_str, "value": time_str})
        start += datetime.timedelta(minutes=increment)
    
    return time_options

# Helper function to extract unique dates from filenames in PostgreSQL
def fetch_unique_dates():
    try:
        # Connect to PostgreSQL (adjust credentials accordingly)
        conn = psycopg2.connect(
            host="172.30.81.47",
            database="aies_dashdb",
            user="coe",
            password="CoEpasswd",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Query the filenames from PostgreSQL
        query = "SELECT filename FROM car;"  # Adjust the query to fit your actual table
        cursor.execute(query)
        filenames = cursor.fetchall()

        # Extract the date part from each filename and keep unique dates
        date_set = set()
        for filename in filenames:
            # Extract date part from filename (e.g., 2024-10-06-12-00.png -> 2024-10-06)
            date_part = filename[0].split('-')[0:3]
            date_str = '-'.join(date_part)  # Combine year, month, day
            date_set.add(date_str)

        # Convert the set to a sorted list of dropdown options
        date_options = [{"label": date, "value": date} for date in sorted(date_set)]

        # Close connection
        cursor.close()
        conn.close()

        return date_options
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# Helper function to connect to PostgreSQL and fetch slot availability
def fetch_parking_data(day, time):
    try:
        # time[1]="-"
        # Connect to PostgreSQL (adjust credentials accordingly)
        conn = psycopg2.connect(
            host="172.30.81.47",
            database="aies_dashdb",
            user="coe",
            password="CoEpasswd",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Query the parking slots availability based on selected day and time
        query = """
        SELECT top_left, top_right, down_left, down_right
        FROM car
        WHERE filename=%s;
        """
        text = "SELECT top_left, top_right, down_left, down_right FROM car WHERE filename='"+day+"-"+time[:2]+"-"+time[3:]+".png';"
        cursor.execute(text)
        result = cursor.fetchone()

        # Close connection
        cursor.close()
        conn.close()
        # return {
        #         "top_left": text,
        #         "top_right": "str(result)",
        #         "bottom_left": "result[2]",
        #         "bottom_right": "result[3]"
        #     }
        if result:
            # Unpack the results
            return {
                "top_left": result[0],
                "top_right": result[1],
                "bottom_left": result[2],
                "bottom_right": result[3]
            }
        else:
            # Return default if no data is found
            return {
                "top_left": "No Data",
                "top_right": "No Data",
                "bottom_left": "No Data",
                "bottom_right": "No Data"
            }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {
            "top_left": "Error",
            "top_right": "Error",
            "bottom_left": "Error",
            "bottom_right": "Error"
        }

# Layout with Data Card
layout = html.Div(
    style={"backgroundColor": "#f4f4f4", "padding": "80px"},
    children=[
        # Header
        html.H1(
            "Dashboard for Finding Motorcycle Parking",
            style={"textAlign": "center", "color": "#4A4A4A", "fontSize": "72px"},
        ),
        
        # Day dropdown (updated to load options from PostgreSQL filenames)
        dcc.Dropdown(
            id="day-select", 
            options=fetch_unique_dates(),  # Fetch unique date options dynamically
            placeholder="Select Day",  # Placeholder shown when no value is selected
            style={
                "width": "50%", 
                "margin": "auto", 
                "marginTop": "20px", 
                "color": "black",
                "textAlign": "center", 
                "fontSize": "20px"
            },
        ),

        # Time dropdown (unchanged)
        dcc.Dropdown(
            id="time-select", 
            options=generate_time_options(),
            placeholder="Select Time",  # Placeholder shown when no value is selected
            style={
                "width": "50%", 
                "margin": "auto", 
                "marginTop": "20px", 
                "color": "black",
                "textAlign": "center", 
                "fontSize": "20px"
            },
        ),

        # Data Card to display the parking availability and selected date/time
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Parking Availability", className="card-title", style={"fontSize": "40px"}),
                    html.P(
                        "Motorcycle parking is available at selected times and locations.",
                        className="card-text",
                        style={"color": "white", "fontSize": "32px"},  # Set color to white
                    ),
                    html.P(id="location", children="Location: Infront of Department of Computer Engineering", style={"color": "white", "fontSize": "32px"}),  # Set color to white
                    html.P(id="slots", children="Available Slots: ...", style={"color": "white", "fontSize": "32px"}),  # Set color to white
                    html.P(id="selected-day", style={"color": "white", "fontSize": "32px"}),  # Set color to white
                    html.P(id="selected-time", style={"color": "white", "fontSize": "32px"}),  # Set color to white
                    html.P(id="last-updated", style={"color": "white", "fontSize": "32px"}),  # Set color to white
                ]
            ),
            style={"width": "50%", "margin": "auto", "marginTop": "40px"},
        ),
    ]
)

# Update the data card based on selected day and time
@dash.callback(
    [Output("selected-day", "children"), 
     Output("selected-time", "children"), 
     Output("last-updated", "children"),
     Output("slots", "children")],  # Add Output for parking slots
    [Input("day-select", "value"), 
     Input("time-select", "value")]
)
def update_data_card(selected_day, selected_time):
    # If no day or time is selected, display a prompt message
    if not selected_day:
        day_text = "Please select a day"
    else:
        day_text = f"Selected Day: {selected_day}"

    if not selected_time:
        time_text = "Please select a time"
    else:
        time_text = f"Selected Time: {selected_time}"

    # Update the current time in UTC+7
    current_time_utc7 = datetime.datetime.now(pytz.utc).astimezone(tz_utc_7)
    last_updated = f"Last Updated: {current_time_utc7.strftime('%Y-%m-%d %H:%M:%S')} (UTC+7)"

    # Fetch parking data from PostgreSQL
    if selected_day and selected_time:
        parking_data = fetch_parking_data(selected_day, selected_time)
        # Format the slots output with line breaks
        slots = (
            f"Available Slots:  "
            f"Top Left: {parking_data['top_left']} ,  "
            f"Top Right: {parking_data['top_right']} ,  "
            f"Bottom Left: {parking_data['bottom_left']} ,  "
            f"Bottom Right: {parking_data['bottom_right']}"
        )
        slots_output = dcc.Markdown(slots)  # Use Markdown for rendering
    else:
        slots_output = "Select both day and time to view available slots."

    return day_text, time_text, last_updated, slots_output