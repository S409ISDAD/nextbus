import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { Region } from "../../models/Places";
import { getRegion } from "../../utils/getPlaces";

const RegionsPage: React.FC = () => {
    const navigate = useNavigate();
    const [region, setRegion] = React.useState<Region>();
    const [loading, setLoading] = React.useState(false);

    const { region_id } = useParams();

    useEffect(() => {
        const getData = async () => {
            if (!region_id) {
                return;
            }
            try {
                setLoading(true);
                const region = await getRegion(region_id);
                setLoading(false);
                if (region) {
                    document.title = `${region.name} | nextbus`;
                    setRegion(region);
                }
            } catch (error) {
                console.log("uh oh", error);
                navigate("/404", { replace: true });
            }
        };

        getData();
    }, [region_id]);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && region && (
                <>
                    <span className="mb-5 text-4xl font-bold">
                        Places in {region.name}
                    </span>
                    <div className="flex flex-col w-full gap-4">
                        <div className="flex flex-col items-center w-full mt-4">
                            {!region ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No Region found.
                                </span>
                            ) : (
                                <div className="gap-4 mb-8 columns-2 md:columns-3 lg:columns-4">
                                    {region.admin_areas?.map((admin_area) => (
                                        <div
                                            key={admin_area.id}
                                            className="mb-2 cursor-pointer break-inside-avoid"
                                            onClick={() => {
                                                navigate(
                                                    `/adminarea/${admin_area.id}`
                                                );
                                            }}>
                                            <span className="underline text-sky-500">
                                                {admin_area.name}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default RegionsPage;
