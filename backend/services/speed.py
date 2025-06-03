# def calculate_speed(self, vehicle, coords, timestamp):
#     lat = coords[0]
#     lon = coords[1]

#     if vehicle in self.loc_history:
#         prev_coords = self.loc_history[vehicle]["coords"]
#         prev_time = self.loc_history[vehicle]["time"]

#         self.loc_history[vehicle]["coords"] = (lat, lon)
#         self.loc_history[vehicle]["time"] = timestamp

#         time_diff = (
#             timestamp - prev_time
#         ).total_seconds() / 3600  # time difference in hours

#         distance = geodesic(prev_coords, (lat, lon)).miles  # distance in miles

#         # print(f"Distance: {distance} miles, Time: {time_diff} hours")

#         speed = (
#             distance / time_diff
#             if time_diff > 0
#             else self.loc_history[vehicle].get("speed", 0)
#         )  # speed in mph

#         old_speed = self.loc_history[vehicle].get("speed", 0)

#         avg_speed = (speed + old_speed) / 2

#         self.loc_history[vehicle]["speed"] = avg_speed

#         return avg_speed
#         return speed
#     else:
#         self.loc_history[vehicle] = {"coords": (lat, lon), "time": timestamp}
#         return 0
