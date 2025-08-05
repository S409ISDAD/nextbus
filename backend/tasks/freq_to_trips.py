from copy import copy
import math

from networkx.utils import pairwise
import numpy as np
import pandas as pd
import partridge as ptg


def seconds_to_gtfs_time(total_seconds):
    if math.isnan(total_seconds):
        return total_seconds  # TODO: What to do here?
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time = list(
        map(lambda x: str(x).rjust(2, "0"), [int(hours), int(minutes), int(seconds)])
    )
    return f"{time[0]}:{time[1]}:{time[2]}"


def freq_to_trips(inpath):
    feed = ptg.load_feed(inpath)

    trips_by_id = {}
    for _, trip in feed.trips.iterrows():
        trips_by_id[trip.trip_id] = dict(trip)

    trip_patterns = {}
    for trip_id, stop_times in feed.stop_times.sort_values("stop_sequence").groupby(
        "trip_id"
    ):
        stops = tuple(stop_times.stop_id)
        mintime = stop_times.arrival_time.min()
        times = tuple(t - mintime for t in stop_times.arrival_time)
        trip_patterns[trip_id] = (stops, times)

    freq_trips = []
    for _, freq in feed.frequencies.iterrows():
        window_start = int(freq.start_time)
        window_end = int(freq.end_time)
        for start in range(window_start, window_end, freq.headway_secs):
            freq_trips.append(
                {
                    "trip_id": freq.trip_id,
                    "start": start,
                }
            )

    new_trips = []
    new_stop_times = []
    for i, ftrip in enumerate(freq_trips, start=1):
        new_trips.append(copy(trips_by_id[ftrip["trip_id"]]))
        new_trips[-1]["trip_id"] = i  # override trip_id

        stops, times = trip_patterns[ftrip["trip_id"]]
        for j in range(len(stops)):
            t = seconds_to_gtfs_time(times[j] + ftrip["start"])
            new_stop_times.append(
                {
                    "trip_id": i,
                    "stop_id": stops[j],
                    "arrival_time": t,
                    "departure_time": t,
                    "stop_sequence": j + 1,
                }
            )

    trips_df = pd.DataFrame(new_trips)
    stop_times_df = pd.DataFrame(new_stop_times)
    empty_frequencies_df = ptg.utilities.empty_df()

    new_feed = ptg.load_raw_feed(inpath)
    new_feed.set("trips.txt", trips_df)
    new_feed.set("stop_times.txt", stop_times_df)
    new_feed.set(
        "frequencies.txt", empty_frequencies_df
    )  # we don't want frequencies.txt

    new_name = inpath.replace(".zip", "_freq_trips.zip")

    ptg.writers.write_feed_dangerously(new_feed, new_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert GTFS frequencies to trips")
    parser.add_argument("inpath", type=str, help="Path to the input GTFS zip file")
    args = parser.parse_args()

    freq_to_trips(args.inpath)
    print(
        f"Converted frequencies to trips and saved to {args.inpath.replace('.zip', '_freq_trips.zip')}"
    )
