import { Marker } from "react-map-gl/maplibre";
import { useNavigate } from "react-router";
import type { MapBus } from "../../models/Bus";
import { TimeSince } from "./TimeSince";
import parse from "html-react-parser";

export function BusMarker({ bus, setPopup }: { bus: MapBus; setPopup: any }) {
    const navigate = useNavigate();

    let className = "bus-marker";

    let angle = bus.heading;

    if (angle != null) {
        if (angle < 180) {
            angle -= 90;
            className += " right";
            // if (bus.vehicle?.right_css) {
            //     background = bus.vehicle.right_css;
            // }
        } else {
            angle -= 270;
        }
    }

    const liveryId = bus.vehicle?.livery;

    if (liveryId) {
        className += ` livery-${liveryId}`;
    }

    return (
        <Marker
            key={bus.trip_id}
            longitude={bus.coords[1]}
            latitude={bus.coords[0]}
            rotation={angle}
            anchor="center"
            style={{
                zIndex: 2,
            }}
            onClick={(e) => {
                e.originalEvent.stopPropagation();
                setPopup({
                    lngLat: [bus.coords[1], bus.coords[0]],
                    content: (
                        <div className="flex flex-col font-bold text-white bg-[#222]">
                            <span
                                className="underline cursor-pointer text-link"
                                onClick={() => navigate(`/buses/${bus.id}`)}>
                                {bus.service?.line_name ?? ""}{bus.destination ? ` to ${bus.destination}` : ""}
                            </span>
                            {bus.vehicle?.name && (
                                <span className="text-xs text-gray-300">
                                    {bus.vehicle.name}
                                </span>
                            )}
                            {bus.vehicle?.features && (
                                <span className="text-xs font-normal text-gray-400">
                                    {parse(bus.vehicle.features)}
                                </span>
                            )}
                            <TimeSince
                                className="text-xs text-gray-300"
                                time={bus.updated}
                            />
                        </div>
                    ),
                });
            }}>
            <svg width="24" height="16" className={className}>
                <text x="12" y="12">
                    {bus.service ? bus.service.line_name : "�"}
                </text>
            </svg>
            {angle == null ? null : <div className="arrow" />}
        </Marker>
    );
}
