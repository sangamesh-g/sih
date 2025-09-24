import folium
from folium import plugins   # 👈 import plugins here
import webbrowser
import os

# Example reports
reports = [
    {"lat": 12.9716, "lon": 77.5946, "problem": "pothole", "priority": 0.9},
    {"lat": 12.9750, "lon": 77.5900, "problem": "flooding", "priority": 0.7},
]

# Start map
m = folium.Map(location=[12.9716, 77.5946], zoom_start=13)

# Add issue markers
for r in reports:
    color = "red" if r["priority"] > 0.8 else "orange"
    folium.Marker(
        [r["lat"], r["lon"]],
        popup=f"{r['problem']} (priority={r['priority']:.2f})",
        icon=folium.Icon(color=color, icon="exclamation-sign"),
    ).add_to(m)

# --- Add User Location (browser will ask permission) ---
plugins.LocateControl(auto_start=True).add_to(m)

# --- Add Navigation / Routing tools ---
plugins.MeasureControl(primary_length_unit='kilometers').add_to(m)

# Save to HTML
map_path = "priority_map.html"
m.save(map_path)

# Open automatically in browser
webbrowser.open("file://" + os.path.realpath(map_path))
print(f"✅ Map saved and opened: {map_path}")
# import folium
# import webbrowser
# import os

# # Example reports
# reports = [
#     {"lat": 17.5357831, "lon": 78.4369031, "problem": "pothole", "priority": 0.9},
#     {"lat": 17.535256239578064, "lon": 78.43470366343523, "problem": "flooding", "priority": 0.7},
# ]

# # Center map
# m = folium.Map(location=[17.5357831,78.4369031], zoom_start=13)

# # Add markers
# for r in reports:
#     color = "red" if r["priority"] > 0.8 else "orange"
#     folium.Marker(
#         [r["lat"], r["lon"]],
#         popup=f"{r['problem']} (priority={r['priority']:.2f})",
#         icon=folium.Icon(color=color, icon="exclamation-sign"),
#     ).add_to(m)

# # Save to HTML
# map_path = "priority_map.html"
# m.save(map_path)

# # Open automatically in browser
# webbrowser.open("file://" + os.path.realpath(map_path))
# print(f"✅ Map saved and opened: {map_path}")
