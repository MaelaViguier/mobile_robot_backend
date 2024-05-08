import socket
import json
import matplotlib.pyplot as plt
import numpy as np

# Ensure the appropriate backend for interactive plotting is set
import matplotlib
matplotlib.use('TkAgg')

# Initialize the plot
plt.ion()  # Turn on interactive plotting
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
line, = ax.plot([], [], 'b.')  # Initial empty plot
ax.set_theta_zero_location('N')  # Set the direction of the 0 degree
ax.set_theta_direction(-1)  # Set the rotation direction (clockwise)
ax.set_ylim(0, 4000)  # Set the radius limit

fig.canvas.draw()  # Perform an initial draw to cache the renderer
plt.show(block=False)  # Display the plot window

def plot_data(data):
    angles = np.array([item[1] for item in data]) * np.pi / 180  # Convert degrees to radians
    distances = np.array([item[2] for item in data])
    line.set_xdata(angles)  # Update angles
    line.set_ydata(distances)  # Update distances
    ax.relim()  # Recalculate limits
    ax.autoscale_view()  # Autoscale view based on the limits
    fig.canvas.draw_idle()  # Redraw the canvas only if idle
    fig.canvas.flush_events()  # Ensure GUI events are processed

def main():
    host = '192.168.1.187'  # Server's IP address
    port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    buffer = ''
    try:
        while True:
            data = client_socket.recv(4096).decode('ascii')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line:
                    scan_data = json.loads(line)
                    print(scan_data)
                    plot_data(scan_data)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
