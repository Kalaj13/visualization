from fileinput import filename

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
import os

# Load data
filename = "Race data/record_opp_103_29745"
df = pd.read_csv(
    filename,
    header=None,
    converters={
        0: ast.literal_eval,
        1: ast.literal_eval,
        2: ast.literal_eval
    }
)


df.columns = ["lidar", "pos", "rpy", "steering_angle", "steering_angle_velocity", "speed", "acceleration", "jerk"]

# Transform LiDAR to global points
def transform_lidar_to_global(x, y, theta, distances, fov_deg=270):
    num_readings = len(distances)
    angles = np.linspace(-np.radians(fov_deg)/2, np.radians(fov_deg)/2, num_readings)

    x_global = x + distances * np.cos(angles + theta)
    y_global = y + distances * np.sin(angles + theta)

    return np.column_stack((x_global, y_global))

# Storage
car_path = []
lidar_points = []

for idx, row in df.iterrows():
    try:
        lidar = np.array(row["lidar"])
        pos = row["pos"]
        rpy = row["rpy"]

        x, y = pos[0], pos[1]
        yaw = rpy[1]

        car_path.append((x, y))

        global_pts = transform_lidar_to_global(x, y, yaw, lidar)
        lidar_points.append(global_pts)
    except Exception as e:
        print(f"Row {idx} skipped due to error: {e}")

# Combine data
car_path_np = np.array(car_path)
lidar_np = np.vstack(lidar_points)

# Plot
plt.figure(figsize=(14, 12))
plt.scatter(lidar_np[:, 0], lidar_np[:, 1], s=0.5, c='black', alpha=0.7, label='LiDAR Points')
plt.plot(car_path_np[:, 0], car_path_np[:, 1], 'r-', linewidth=1.5, label='Car Path')

# Optional heatmap
plt.hexbin(lidar_np[:, 0], lidar_np[:, 1], gridsize=1000, cmap='inferno', bins='log', alpha=0.5)

# Labels
plt.text(car_path_np[0][0], car_path_np[0][1], "START", fontsize=14, color='green', weight='bold')
plt.text(car_path_np[-1][0], car_path_np[-1][1], "END", fontsize=14, color='blue', weight='bold')

plt.axis('equal')
plt.xlabel("X")
plt.ylabel("Y")
plt.grid(True)
plt.title(f"File: {os.path.basename(filename)}")
plt.suptitle("Race track: exo5_obst")
#plt.suptitle("LiDAR Map and Car Path")
plt.legend()
plt.tight_layout()
plt.show()
