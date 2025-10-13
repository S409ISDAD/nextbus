import React, { useEffect } from "react";
import { useNavigate } from "react-router";
import type { Region } from "../../models/Places";
import { getRegions } from "../../utils/getPlaces";

const RegionsPage: React.FC = () => {
    const navigate = useNavigate();
    const [regions, setRegions] = React.useState<Region[]>();
    const [loading, setLoading] = React.useState(false);

    useEffect(() => {
        document.title = `regions | nextbus`;
        const getData = async () => {
            try {
                setLoading(true);
                const regions = await getRegions();
                setLoading(false);
                if (regions) {
                    setRegions(regions);
                }
            } catch (error) {
                console.log("uh oh", error);
            }
        };

        getData();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            <span className="mb-5 text-4xl font-bold">Regions</span>

            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && regions && (
                <div className="flex flex-col w-full gap-4">
                    <div className="flex flex-col items-center w-full mt-4">
                        {regions.length === 0 ? (
                            <span className="w-full mb-5 text-sm text-center text-gray-400">
                                No places found.
                            </span>
                        ) : (
                            <div className="gap-10 mb-8 columns-2 md:columns-3 lg:columns-4">
                                {regions.map((region) => (
                                    <div
                                        key={region.id}
                                        className="mb-2 cursor-pointer break-inside-avoid"
                                        onClick={() => {
                                            navigate(`/region/${region.id}`);
                                        }}>
                                        <span className="underline text-link">
                                            {region.name}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default RegionsPage;
