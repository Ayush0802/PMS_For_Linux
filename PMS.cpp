#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <dirent.h>
#include <sys/types.h>
#include <unistd.h>
#include <iomanip>
#include <ctime>
#include <cstdlib>
#include <cstdio>


// Define process states
enum ProcessState {
    PS_RUNNING,
    PS_SLEEPING,
    PS_WAITING,
    PS_ZOMBIE,
    PS_STOPPED,
    PS_UNKNOWN,
};

const std::string state_names[] = {
    "Running",
    "Sleeping",
    "Waiting",
    "Zombie",
    "Stopped",
    "Unknown",
};

const std::string colors[] = {
    "\x1B[31m",  // Red
    "\x1B[32m",  // Green
    "\x1B[33m",  // Yellow
    "\x1B[34m",  // Blue
    "\x1B[35m",  // Magenta
    "\x1B[36m",  // Cyan
};

const std::string reset_color = "\x1B[0m";

// Function to convert state character to ProcessState
ProcessState charToProcessState(char c) {
    switch (c) {
        case 'R':
            return PS_RUNNING;
        case 'S':
            return PS_SLEEPING;
        case 'D':
            return PS_WAITING;
        case 'Z':
            return PS_ZOMBIE;
        case 'T':
            return PS_STOPPED;
        default:
            return PS_UNKNOWN;
    }
}

// Function to get process state for a given PID
ProcessState getProcessState(int pid) {
    std::ifstream stat_file("/proc/" + std::to_string(pid) + "/stat");
    if (!stat_file) {
        return PS_UNKNOWN;
    }

    std::string line;
    std::getline(stat_file, line);
    std::istringstream iss(line);
    std::vector<std::string> tokens;
    for (std::string token; iss >> token;) {
        tokens.push_back(token);
    }

    if (tokens.size() >= 3) {
        return charToProcessState(tokens[2][0]);
    }

    return PS_UNKNOWN;
}

// Function to print a colored bar chart slice with percentage up to 3 decimal places
void printPieSlice(const std::string& label, double percent, const std::string& color) {
    std::cout << color << label << " ";
    for (int i = 0; i < static_cast<int>(percent); ++i) {
        std::cout << "█";  // Use a block character as a representation
    }
    std::cout << " " << std::fixed << std::setprecision(3) << percent << "%" << reset_color << std::endl;
}

// Function to run the top command and capture its output
std::string runTopCommand() {
    std::string result;
    FILE* pipe = popen("top -n 1 -b", "r");
    if (!pipe) {
        return "Error running top command.";
    }

    char buffer[128];
    while (!feof(pipe)) {
        if (fgets(buffer, 128, pipe) != nullptr) {
            result += buffer;
        }
    }

    pclose(pipe);
    return result;
}

int main() {
    std::cout << "Process Status on Ubuntu" << std::endl;

    DIR* dir;
    struct dirent* ent;

    // Open the /proc directory
    dir = opendir("/proc");
    if (dir == nullptr) {
        std::cerr << "Error opening /proc directory" << std::endl;
        return 1;
    }

    // Map to store the process state counts
    std::map<ProcessState, int> state_counts;
    std::map<int, std::pair<ProcessState, std::string>> process_info;

    // Read each entry in the /proc directory
    while ((ent = readdir(dir)) != nullptr) {
        // Check if the entry is a directory and represents a numeric process ID
        std::string name = ent->d_name;
        if (name.find_first_not_of("0123456789") == std::string::npos) {
            int pid = std::stoi(name);
            ProcessState state = getProcessState(pid);
            state_counts[state]++;
            process_info[pid] = {state, name};
        }
    }

    closedir(dir);

    // Calculate the total number of processes
    int total_processes = 0;
    for (const auto& entry : state_counts) {
        total_processes += entry.second;
    }

    // Create an output file stream
    std::ofstream output_file("process_status.txt");
    if (!output_file.is_open()) {
        std::cerr << "Error opening output file for writing" << std::endl;
        return 1;
    }

    output_file << "Process Status and Names:" << std::endl;
    for (const auto& entry : process_info) {
        int pid = entry.first;
        ProcessState state = entry.second.first;
        std::string name = entry.second.second;
        output_file << "PID " << pid << ": " << name << " (" << state_names[state] << ")" << std::endl;
    }

    // Print process state counts as a pie chart to the file
    int index = 0;
    for (const auto& entry : state_counts) {
        ProcessState state = entry.first;
        int count = entry.second;
        double percent = (count * 100.0) / total_processes;

        output_file << state_names[state] << " " << std::fixed << std::setprecision(3) << percent << "%" << std::endl;
        index = (index + 1) % (sizeof(colors) / sizeof(colors[0]));
    }

    // Close the output file
    output_file.close();

    // Get and print real-time process information from the top command
    std::string topOutput = runTopCommand();
    output_file.open("top_output.txt");
    if (output_file.is_open()) {
        output_file << "Real-time Process Information (Top Output):\n" << topOutput << std::endl;
        output_file.close();
    } else {
        std::cerr << "Error opening output file for writing top command output" << std::endl;
        return 1;
    }

    // Open the output file using the system's default text editor
    system("xdg-open process_status.txt");
    system("xdg-open top_output.txt");

    system("python3 graph.py");

    return 0;
}