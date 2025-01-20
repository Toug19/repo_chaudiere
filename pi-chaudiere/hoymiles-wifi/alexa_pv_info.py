# integrated directly in flask_python code

from datetime import datetime, timezone
import re

def process_photovoltaic_data(file_path):
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split readings based on blocks starting with "device_serial_number" and ending with empty lines
    readings = content.strip().split("\n\n")
    
    # Prepare to track results
    power_sums = []
    timestamps = []
    
    # Process each reading
    for reading in readings:
        if "device_serial_number" not in reading:
            continue
        
        # Extract timestamp
        timestamp_match = re.search(r'timestamp:\s*(\d+)', reading)
        timestamp = int(timestamp_match.group(1)) if timestamp_match else None
        if timestamp:
            timestamps.append(timestamp)
        
        # Extract active_power values from sgs_data
        active_powers = [
            int(match.group(1)) * 0.1  # Apply the factor of 0.1
            for match in re.finditer(r'sgs_data\s*{[^}]*?active_power:\s*(\d+)', reading)
        ]
        
        # Sum active powers if they exist, otherwise append 0
        power_sums.append(sum(active_powers) if active_powers else 0)
    
    # Handle cases where no readings are available
    if not power_sums or not timestamps:
        return None, 0, 0, None

    # Analyze the last reading
    last_power_sum = power_sums[-1]
    last_timestamp = timestamps[-1]
    
    # Convert last timestamp to timezone-aware datetime
    last_datetime = datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
    
    # Calculate the average of the last 4 readings
    last_4_avg = sum(power_sums[-4:]) / min(4, len(power_sums))
    
    return last_timestamp, last_power_sum, last_4_avg, last_datetime
