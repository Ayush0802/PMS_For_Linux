import matplotlib.pyplot as plt
import time

# Initialize variables to store process state counts
state_counts = {
    "Running": 0,
    "Sleeping": 0,
    "Waiting": 0,
    "Unknown": 0,
}

# Read the "process_status.txt" file
with open("process_status.txt", "r") as file:
    lines = file.readlines()
    state_data_started = False

    for line in lines:
        line = line.strip()
        if line == "Process Status and Names:":
            state_data_started = True
        elif state_data_started:
            parts = line.split()
            if len(parts) == 2:
                state, percent = parts
                state_counts[state] = float(percent.strip("%"))

# Extract data for the pie chart
states = list(state_counts.keys())
counts = list(state_counts.values())

# Create a pie chart
plt.pie(counts, labels=states, colors=['blue', 'green', 'orange', 'red'], autopct='%1.1f%%')
plt.title('Process State Distribution')
plt.axis('equal')  # Equal aspect ratio ensures that the pie is drawn as a circle.
plt.show()


