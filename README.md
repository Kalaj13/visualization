# LiDAR Path and Obstacle Visualizer

This Python application visualizes a car's path and the surrounding environment using LiDAR sensor data. It reads a CSV log file containing LiDAR readings, position, and orientation data, and produces a 2D top-down map showing the car’s movement and perceived obstacles.

---

## 📦 Features

- ✅ Plots the car's path based on positional data
- ✅ Projects LiDAR points to global coordinates using yaw orientation
- ✅ Displays LiDAR beams for clearer obstacle visualization
- ✅ Annotates the start and end points of the car's path
- ✅ Dynamically displays the loaded filename as the map title

---

## 📁 Input File Format

The application expects a `.csv` file with the following columns:

| Column Index | Description                | Example                                |
|--------------|----------------------------|----------------------------------------|
| 0            | LiDAR readings (list)      | `[-0.81, -0.82, ..., -0.79]`           |
| 1            | Position (x, y, z)         | `[1.2, 0.5, 0.0]`                       |
| 2            | Orientation (roll, pitch, yaw) | `[0.0, 0.0, 1.57]`                    |
| 3–7          | Optional motion data       | Steering angle, speed, acceleration... |

---

## 🚀 How to Run

1. **Install dependencies** (Python 3.8+ recommended):

   ```bash
   pip install pandas matplotlib
