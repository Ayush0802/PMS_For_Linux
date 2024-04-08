#importing required libraries
import os
import subprocess
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import signal

#create a class with constants representing different process states
class ProcessState:
    PS_RUNNING = 'R'
    PS_SLEEPING = 'S'
    PS_WAITING = 'D'
    PS_ZOMBIE = 'Z'
    PS_STOPPED = 'T'
    PS_UNKNOWN = 'U'

#create a dictionary which stores the state names
state_names = {
    ProcessState.PS_RUNNING: "Running",
    ProcessState.PS_SLEEPING: "Sleeping",
    ProcessState.PS_WAITING: "Waiting",
    ProcessState.PS_ZOMBIE: "Zombie",
    ProcessState.PS_STOPPED: "Stopped",
    ProcessState.PS_UNKNOWN: "Unknown"
}

# Create function to convert state character to actual Process State name
def charToProcessState(c):
    return {
        'R': ProcessState.PS_RUNNING,
        'S': ProcessState.PS_SLEEPING,
        'D': ProcessState.PS_WAITING,
        'Z': ProcessState.PS_ZOMBIE,
        'T': ProcessState.PS_STOPPED
    }.get(c, ProcessState.PS_UNKNOWN)

# Create function to get process state for a given PID
def getProcessState(pid):
    try:
        #to fetch the information of status of process of particular pid
        with open(f"/proc/{pid}/stat") as stat_file: 
            line = stat_file.readline()
            tokens = line.split()
            if len(tokens) >= 3:
                return charToProcessState(tokens[2][0])
    except FileNotFoundError:
        pass
    return ProcessState.PS_UNKNOWN

# Create function to run the top command and capture its output
def runTopCommand():
    try:
        # to fetch the top commad output (Process Attributes) in result
        result = subprocess.check_output(["top", "-n", "1", "-b"], universal_newlines=True) 
        return result
    except subprocess.CalledProcessError:
        return "Error running top command."

# Create function to parse the top output and extract relevant information
def parseTopOutput(output):
    lines = output.splitlines()
    start_line = 7  
    data = [line.split() for line in lines[start_line:]]
    return data

# Create function to update the top output table
def update_top_output_table():
    top_output_text.delete(*top_output_text.get_children())

    top_output = runTopCommand() #to fetch process attributes as a string
    data = parseTopOutput(top_output) #break the string 

    for row in data:
        top_output_text.insert("", "end", values=row)

    top_output_text.tag_configure("header", background="gray")
    root.after(1000, update_top_output_table)  # Update every 1 seconds

# Create function to update the process status table
def update_process_status_table():
    process_info = {} # Create an empty dictionary to store the process data.
    for pid in os.listdir("/proc"):  # fetch the process id using '/proc'
        if pid.isdigit():
            pid = int(pid)
            state = getProcessState(pid)
            try:
                # to fetch the process name of particular pid
                with open(f"/proc/{pid}/comm", "r") as comm_file:
                    process_name = comm_file.readline().strip()
            except FileNotFoundError:
                process_name = "Unknown"
            process_info[pid] = (state, pid, process_name)

    process_status_text.delete(*process_status_text.get_children())

    status_counts = {} #create dictionary to store count of each state
    for pid, (state, pid_number, process_name) in process_info.items():
        state_name = state_names.get(state, "Unknown")
        process_status_text.insert("", "end", values=(pid_number, process_name, state_name))

        # Count the occurrences of each state
        if state_name in status_counts:
            status_counts[state_name] += 1
        else:
            status_counts[state_name] = 1

    # Update the existing bar chart with new data
    statuses = list(status_counts.keys())
    counts = [status_counts[state] for state in statuses]

    # Create a bar chart with different colors
    ax.clear()
    colors = random.sample(bar_colors, len(statuses))
    ax.bar(statuses, counts, color=colors)
    ax.set_xlabel("Status")
    ax.set_ylabel("Count")
    ax.set_title("Process Status Bar Chart")

    # Add the number of processes to the x-axis labels
    x_labels = [f"{state}\n({count})" for state, count in zip(statuses, counts)]
    ax.set_xticklabels(x_labels)

    chart_canvas.draw()

    root.after(1000, update_process_status_table)  # Update every 1 seconds

paused_pids = []

# Create function to pause a process
def pause_process(pid):
    try:
        os.kill(pid, signal.SIGSTOP)    #function call to pause the process with pid
        paused_pids.append(pid)
    except ProcessLookupError:
        print(f"No process with PID {pid} found.")

# Create function to resume a process  
def resume_process(pid):
    if pid in paused_pids:
        try:
            os.kill(pid, signal.SIGCONT)  #function call to resume the process with pid
            paused_pids.remove(pid)
        except ProcessLookupError:
            print(f"No process with PID {pid} found.")
    else:
        print(f"Process {pid} is not paused.")

# Creaet function to kill a process with a given PID
def kill_process():
    pid = entry_pid.get()
    try:
        subprocess.run(["kill", "-9", str(pid)]) #function call to kill the process with pid
    except subprocess.CalledProcessError:
        print(f"Error killing process with PID {pid}.")

# Create the main window
root = tk.Tk()
root.title("Process Status")

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create a frame for the process status and graph
frame1 = tk.Frame(root)
frame1.grid(row=0, column=0, sticky="nsew")

# Create a frame for process attributes table
frame2 = tk.Frame(root)
frame2.grid(row=1, column=0, sticky="nsew")

# Create a table to display the process status
process_status_text = ttk.Treeview(frame1, columns=("PID", "Name", "Status"), show="headings")
process_status_text.heading("#1", text="PID")
process_status_text.heading("#2", text="Name")
process_status_text.heading("#3", text="Status")
process_status_text.pack(side="left", expand=True, fill="both")

chart_frame = ttk.Frame(frame1)
chart_frame.pack(side="right", expand=True, fill="both")

# Create an initial graph for the chart
fig, ax = plt.subplots(figsize=(6, 4))
chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
chart_canvas.get_tk_widget().pack(expand=True, fill="both")

bar_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

# Create a table to display top command output in table format
column_headings = ["PID", "USER", "PR", "NI", "VIRT", "RES", "SHR", "S", "%CPU", "%MEM", "TIME+", "COMMAND"]
top_output_text = ttk.Treeview(frame2, columns=column_headings, show="headings")
top_output_text.pack(expand=True, fill="both")

column_widths = [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 70, 90] 

for heading, width in zip(column_headings, column_widths):
    top_output_text.heading(heading, text=heading)
    top_output_text.column(heading, width=width)

for heading in column_headings:
    top_output_text.heading(heading, text=heading)

style = ttk.Style()
style.configure("Treeview.Heading", font=("Helvetica", 12))
style.configure("Treeview", font=("Helvetica", 11))

# Create a label, entry, and button for entering and killing a specific PID
label_pid = tk.Label(frame2, text="Enter PID to Kill:")
label_pid.pack(side="left", padx=(10, 5))

entry_pid = tk.Entry(frame2)
entry_pid.pack(side="left", padx=(0, 10))

button_kill = tk.Button(frame2, text="Kill Process", command=kill_process)
button_kill.pack(side="left")

label_pid2 = tk.Label(frame2, text="Enter PID to Pause:")
label_pid2.pack(side="left", padx=(10, 5))

entry_pause_pid = ttk.Entry(frame2) 
entry_pause_pid.pack(side="left", padx=(0, 10))

button_pause = ttk.Button(frame2, text="Pause Process", command=lambda: pause_process(int(entry_pause_pid.get()))) 
button_pause.pack(side="left")

label_pid3 = tk.Label(frame2, text="Enter PID to Resume:")
label_pid3.pack(side="left", padx=(10, 5))

entry_resume_pid = ttk.Entry(frame2)
entry_resume_pid.pack(side="left", padx=(0, 10))

button_resume = ttk.Button(frame2, text="Resume Process", command=lambda: resume_process(int(entry_resume_pid.get())))
button_resume.pack(side="left")

# Adjust the layout to make room for the new widgets
frame2.grid_columnconfigure(1, weight=1)

#update process status table
update_process_status_table()

#update top output table
update_top_output_table()

root.mainloop()