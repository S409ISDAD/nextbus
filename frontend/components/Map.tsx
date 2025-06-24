import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { cn } from "../utils/cn";

export default function MapView({
    className,
}: React.PropsWithChildren<{ className?: string }>) {
    return (
        <div className={cn(className)}>
            <MapContainer
                center={[51.505, -0.09]}
                zoom={13}
                style={{ height: "400px", width: "400px" }}>
                <TileLayer
                    attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={[51.505, -0.09]}>
                    <Popup>Bus is here</Popup>
                </Marker>
            </MapContainer>
        </div>
    );
}
