# permet de tracer un graphique de production et génére des png 

import pandas as pd
import matplotlib.pyplot as plt

def plot_graphs(file_path, x_column, y_columns, x_label, y_labels, titles, output_files):
    # Load the data from the CSV file
    data = pd.read_csv(file_path)

    # Convert the x_column to datetime format if it's a timestamp
    if 'timestamp' in x_column:
        data[x_column] = pd.to_datetime(data[x_column])

    # Plot each graph
    for y_column, y_label, title, output_file in zip(y_columns, y_labels, titles, output_files):
        plt.figure(figsize=(12, 6))
        plt.plot(data[x_column], data[y_column], marker='o', linestyle='-')
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot as an image file
        plt.savefig(output_file)

        # Display the plot
        plt.show()

# Example usage
file_path = 'PV_data.csv'  # Path to your CSV file
x_column = 'timestamp_readable'  # Column for the x-axis
y_columns = ['totalACPower', 'totalDCPower']  # Columns for the y-axis
x_label = 'Time'
y_labels = ['Total AC Power (W)', 'Total DC Power (W)']
titles = ['Total AC Power vs Time', 'Total DC Power vs Time']
output_files = ['total_ac_power_vs_time.png', 'total_dc_power_vs_time.png']

plot_graphs(file_path, x_column, y_columns, x_label, y_labels, titles, output_files)