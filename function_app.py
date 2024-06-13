import azure.functions as func  # Import Azure Functions SDK
import logging  # Import logging module to enable logging
import json  # Import JSON module to handle JSON operations
from datetime import datetime, timedelta  # Import datetime modules for handling date and time
from collections import defaultdict  # Import defaultdict to handle default values in dictionaries
import urllib.request  # Import urllib module for handling URL requests
import os  # Import os module to interact with the operating system
import ssl  # Import ssl module for handling SSL/TLS certificates

# Initialize the Azure Function app with a specific authentication level
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Function to get the earliest and latest dates from a list of messages
def get_earliest_and_latest_dates(messages):
    # Convert message dates from ISO format to datetime objects
    dates = [datetime.fromisoformat(message['date'].replace('Z', '+00:00')) for message in messages]
    earliest_date = min(dates)  # Find the earliest date
    latest_date = max(dates)  # Find the latest date
    return earliest_date, latest_date

# Function to get the day of the week for a given date
def get_day_of_week(date):
    return date.strftime('%A')

# Function to group messages by the week they were sent
def group_messages_by_week(messages):
    def get_week_start(date):
        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        return start_of_week.strftime('%Y-%m-%d')

    grouped_messages = defaultdict(list)
    for message in messages:
        week_start = get_week_start(message['date'])
        grouped_messages[week_start].append(message)

    text_messages = []
    for week_start, msgs in grouped_messages.items():
        text_out = f"Week starting on {week_start}:"
        for msg in msgs:
            text_out += f"\n  {msg['date']} - {msg['sender']} to {', '.join(msg['recipients'])}: {msg['body']}"
        text_messages.append(text_out)

    return grouped_messages, text_messages

# Function to group messages by the month they were sent
def group_messages_by_month(messages):
    def get_month(date):
        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        return date_obj.strftime('%Y-%m')

    grouped_messages = defaultdict(list)
    for message in messages:
        month = get_month(message['date'])
        grouped_messages[month].append(message)

    text_messages = []
    for month_start, msgs in grouped_messages.items():
        text_out = f"Month starting on {month_start}:"
        for msg in msgs:
            text_out += f"\n  {msg['date']} - {msg['sender']} to {', '.join(msg['recipients'])}: {msg['body']}"
        text_messages.append(text_out)

    return grouped_messages, text_messages

# Function to group messages by a custom interval of days
def group_messages_by_interval(messages, interval_days):
    def get_interval_start_date(date, interval_days):
        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        start_of_year = datetime(date_obj.year, 1, 1)
        days_since_start_of_year = (date_obj - start_of_year).days
        interval_number = days_since_start_of_year // interval_days
        interval_start_date = start_of_year + timedelta(days=interval_number * interval_days)
        return interval_start_date.strftime('%Y-%m-%d')

    grouped_messages = defaultdict(list)
    for message in messages:
        interval_start_date = get_interval_start_date(message['date'], interval_days)
        grouped_messages[interval_start_date].append(message)

    text_messages = []
    for start_date, msgs in grouped_messages.items():
        text_out = f"Period starting on {start_date}:"
        for msg in msgs:
            text_out += f"\n  {msg['date']} - {msg['sender']} to {', '.join(msg['recipients'])}: {msg['body']}"
        text_messages.append(text_out)

    return grouped_messages, text_messages

# Function to allow self-signed HTTPS certificates
def allow_self_signed_https(allowed):
    # Enable the use of self-signed certificates if allowed and not already set by environment
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allow_self_signed_https(True)  # Call the function to allow self-signed HTTPS certificates

# Function to request a completion from an AI model
def request_completion(rsmf_str, summary_prompt, temp):
    data = {
        "messages": [
            {"role": "system", "content": "Your role is to concisely summarise work chats."},
            {"role": "user", "content": "All responses will be in valid HTML format. All dotpoints or lists will use the <ul>[list]</ul>tag. It should be in the following format:<h3>[Date Start in dd-mmm-yyy7] - [Date End in dd-mmm-yyy7]</h3><p>[Content]</p>"},
            {"role": "system", "content": "Only show dotpoint or lists if explicity asked for."},
            {"role": "user", "content": summary_prompt},
            {"role": "user", "content": rsmf_str}
        ],
        "max_tokens": 300,
        "temperature": float(temp),
        "top_p": 0.1,
        "best_of": 1,
        "presence_penalty": 0,
        "use_beam_search": "false",
        "ignore_eos": "false",
        "skip_special_tokens": "false",
        "logprobs": "false"
    }

    body = str.encode(json.dumps(data))  # Encode the data to JSON
    url = #Your LLM URL here...  # Placeholder for LLM URL
    api_key = #Your API key here...  # Placeholder for API key
   
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")  # Raise an exception if API key is missing

    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key}  # Set request headers
    req = urllib.request.Request(url, body, headers)  # Create the request

    try:
        response = urllib.request.urlopen(req)  # Send the request
        result = json.loads(response.read())  # Parse the JSON response
        return result['choices'][0]['message']['content']  # Extract content from the response
    except urllib.error.HTTPError as error:
        return error.read().decode("utf8", 'ignore')  # Handle HTTP errors

# Function to handle requests for message summarisation based on different intervals
def request_handler(interval, rsmf, temp, summary_prompt="Summarise the below chat. List main events. List action points."):
    messages = rsmf['messages']  # Extract messages from the request
    rsmf_response = []

    if interval.lower() == "week":
        weeks = group_messages_by_week(messages)[1]  # Get text messages grouped by week
        weeks_json = group_messages_by_week(messages)[0]  # Get JSON data grouped by week
        for i in range(len(weeks)):
            rsmf_response.append({"date": list(weeks_json.keys())[i], "completion": request_completion(weeks[i], summary_prompt, temp)})  # Process each week's messages
        return rsmf_response
    elif interval.lower() == "month":
        months = group_messages_by_month(messages)[1]  # Get text messages grouped by month
        months_json = group_messages_by_month(messages)[0]  # Get JSON data grouped by month
        for i in range(len(months)):
            rsmf_response.append({"date": list(months_json.keys())[i], "completion": request_completion(months[i], summary_prompt, temp)})  # Process each month's messages
        return rsmf_response
    elif interval.isdigit():
        interval_days = int(interval)
        intervals = group_messages_by_interval(messages, interval_days)[1]  # Get text messages grouped by custom interval
        intervals_json = group_messages_by_interval(messages, interval_days)[0]  # Get JSON data grouped by custom interval
        for i in range(len(intervals)):
            rsmf_response.append({"date": list(intervals_json.keys())[i], "completion": request_completion(intervals[i], summary_prompt, temp)})  # Process each interval's messages
        return rsmf_response
    else:
        return "Invalid interval. Please enter either 'week' or 'month'."

# Azure Function to handle HTTP trigger requests
@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')  # Log the processing of a request
    # Get the parameters from the body of the request
    req_body = req.get_json()
    prompt = req_body.get('prompt')
    interval = req_body.get('interval')
    rsmf = req_body.get('rsmf')
    temp = req_body.get('temp')

    if not all([prompt, interval, rsmf]):
        return func.HttpResponse("Missing required parameters", status_code=400)  # Return error if required parameters are missing

    try:
        response = request_handler(interval, rsmf, temp, prompt)  # Handle the request based on the interval
        return func.HttpResponse(json.dumps(response), mimetype="application/json", status_code=200)  # Return the response in JSON format
    except json.JSONDecodeError:
        logging.error("Invalid JSON format")  # Log JSON format errors
        return func.HttpResponse("Invalid JSON format", status_code=400)  # Return error for invalid JSON
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")  # Log other exceptions
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)  # Return error for other exceptions
