from geopy.distance import geodesic



async def calculate_distances(stops: list) -> list[float]:
    distances = []

    for stop in stops:
        track = stop["track"]

        if track:
            dist = 0
            for i, point in enumerate(track):
                if i + 1 == len(track):
                    break
                dist += geodesic(point, track[i + 1]).m
            distances.append(dist)

    return distances


async def estimate_speeds(distances: list[float]) -> list[int]:
    speeds = []
    for dist in distances:
        if dist < 200:
            speeds.append(5)
        elif dist < 400:
            speeds.append(8)
        elif dist < 700:
            speeds.append(12)
        elif dist < 1200:
            speeds.append(15)
        elif dist < 2000:
            speeds.append(18)
        else:
            speeds.append(22)

    return speeds


async def calculate_time_frac(distances: list[float], speeds: list[int]) -> list[float]:
    time_per_segment = []

    for speed, dist in zip(speeds, distances):
        time = dist / speed
        time = max(30, time)
        time_per_segment.append(time)

    total_time = sum(time_per_segment)

    frac = []

    for segment in time_per_segment:
        frac.append(segment / total_time)

    return frac


async def redistribute(fracs: list[float], stops: list):
    start_time = stops[0]["aimed_time"]
    end_time = stops[-1]["aimed_time"]
    total_time = end_time - start_time

    new_times = []
    new_times.append(start_time)
    elapsed = 0
    for frac in fracs:
        elapsed += round(frac * total_time)
        new_times.append(int(start_time + elapsed))
    return new_times


async def check_similarity(stops: list, new_times: list[int], distances, speeds):
    errors: list = []
    for stop, new_time in zip(stops, new_times):
        diff = new_time - stop["aimed_time"]

        errors.append(diff)

    error = sum(errors) / len(errors)

    output = ""
    for error, dist, speed in zip(errors, distances, speeds):
        output += f"error: {error} dist: {round(dist)}m speed: {speed}m/s \n"

    print(output)
    mean_error = sum(errors) / len(errors)
    mean_abs_error = sum(abs(e) for e in errors) / len(errors)

    import statistics

    std_error = statistics.stdev(errors)

    print(f"Mean error: {mean_error:.1f} seconds")
    print(f"Mean absolute error: {mean_abs_error:.1f} seconds")
    print(f"Standard deviation: {std_error:.1f} seconds")


async def recalculate_timetable(stops: list, journey_id: int, r):
    async def calculate(stops: list):
        distances = await calculate_distances(stops)

        speeds = await estimate_speeds(distances)

        fracs = await calculate_time_frac(distances, speeds)

        new_times = await redistribute(fracs, stops)

        await check_similarity(stops, new_times, distances, speeds)

        return new_times

    # new_times = await get_cached(
    #     key=f"times:{journey_id}",
    #     func=lambda *args: calculate(*args),
    #     args=(stops,),
    #     exp=TIMETABLE_CACHE,
    #     r=r,
    # )

    new_times = await calculate(stops)

    for i, stop in enumerate(stops):
        stops[i]["aimed_time"] = new_times[i]

    return stops
