import tkinter as tk
from tkinter import ttk, messagebox
import math
import requests
from geopy.distance import distance
from geopy.point import Point
import tkintermapview

def get_ground_altitude(lat, lon):
    try:
        res = requests.get("https://api.open-elevation.com/api/v1/lookup",
                         params={"locations": f"{lat},{lon}"}, timeout=5)
        res.raise_for_status()
        return res.json()["results"][0]["elevation"]
    except Exception as e:
        messagebox.showerror("Altitude Error", f"Could not fetch ground altitude:\n{e}")
        return None

def calculate_drop():
    try:
        m = float(entry_weight.get()) / 1000  # g to kg
        altitude = float(entry_altitude.get())
        v_horizontal = float(entry_speed.get())
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
        heading = float(entry_heading.get()) % 360

        target_ground_alt = get_ground_altitude(lat, lon)
        if target_ground_alt is None:
            return

        h = altitude - target_ground_alt
        if h <= 0:
            messagebox.showerror("Error", f"Plane is below or at ground level.\n\nPlane Altitude (MSL): {altitude} m\nTarget Ground Altitude: {target_ground_alt} m")
            return

        # Terminal velocity with drag
        rho = 1.225  # air density kg/m³
        Cd = 0.8     # drag coefficient (cylinder)
        r = 0.025    # radius in m
        A = math.pi * r**2
        g = 9.81

        v_terminal = math.sqrt((2 * m * g) / (rho * A * Cd))
        t_fall = (v_terminal / g) * math.tanh((g * h) / (v_terminal**2))

        drop_distance = v_horizontal * t_fall  # in meters
        target_point = Point(lat, lon)
        drop_point = distance(meters=drop_distance).destination(target_point, (heading + 180) % 360)

        # Update map
        map_widget.set_position(lat, lon)
        map_widget.set_zoom(17)
        map_widget.delete_all_marker()
        map_widget.set_marker(lat, lon, text="🎯 Target")
        map_widget.set_marker(drop_point.latitude, drop_point.longitude, text="📦 Drop Point")

        # Show result
        result_text.set(
            f"Target Ground Altitude: {target_ground_alt:.1f} m\n"
            f"Plane Altitude (MSL): {altitude:.1f} m\n"
            f"Fall Height: {h:.1f} m\n"
            f"Fall Time: {t_fall:.2f} s\n"
            f"Drop Distance: {drop_distance:.1f} m\n"
            f"Drop Point:\n{drop_point.latitude:.6f}, {drop_point.longitude:.6f}"
        )

    except Exception as e:
        messagebox.showerror("Input Error", str(e))

def on_map_click(coords):
    """Set target location when map is clicked"""
    entry_lat.delete(0, tk.END)
    entry_lat.insert(0, f"{coords[0]:.6f}")
    entry_lon.delete(0, tk.END)
    entry_lon.insert(0, f"{coords[1]:.6f}")
    map_widget.delete_all_marker()
    map_widget.set_marker(coords[0], coords[1], text="🎯 Target")

# Main window setup
root = tk.Tk()
root.title("UAV Payload Drop Calculator")
root.state('zoomed')  # Start maximized

# Configure grid weights for resizing
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Left panel
left_frame = ttk.Frame(root, padding=10)
left_frame.grid(row=0, column=0, sticky="nsew")

fields = [
    ("Payload Weight (g):", "entry_weight"),
    ("Plane Altitude (MSL) (m):", "entry_altitude"),
    ("Plane Speed (m/s):", "entry_speed"),
    ("Heading (°):", "entry_heading"),
    ("Target Latitude:", "entry_lat"),
    ("Target Longitude:", "entry_lon"),
]

entries = {}
for i, (label_text, var_name) in enumerate(fields):
    ttk.Label(left_frame, text=label_text).grid(row=i, column=0, sticky="e", pady=2)
    entry = ttk.Entry(left_frame, width=20)
    entry.grid(row=i, column=1, pady=2)
    entries[var_name] = entry

entry_weight = entries["entry_weight"]
entry_altitude = entries["entry_altitude"]
entry_speed = entries["entry_speed"]
entry_heading = entries["entry_heading"]
entry_lat = entries["entry_lat"]
entry_lon = entries["entry_lon"]

# Set default values
entry_weight.insert(0, "500")
entry_altitude.insert(0, "100")
entry_speed.insert(0, "30")
entry_heading.insert(0, "0")

# Calculate button
ttk.Button(left_frame, text="Calculate Drop Point", command=calculate_drop).grid(
    row=len(fields), column=0, columnspan=2, pady=10)

# Results display
result_text = tk.StringVar()
ttk.Label(left_frame, textvariable=result_text, justify="left", padding=5, 
         foreground="blue").grid(row=len(fields)+1, column=0, columnspan=2)

# Map widget
map_widget = tkintermapview.TkinterMapView(root, width=800, height=600, corner_radius=0)
map_widget.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

# Configure map
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
map_widget.set_position(39.8283, -98.5795)  # Center of US
map_widget.set_zoom(4)  # Show all of North America
map_widget.add_left_click_map_command(on_map_click)  # Click to place marker

root.mainloop()
