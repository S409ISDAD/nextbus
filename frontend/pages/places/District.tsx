import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { District } from "../../models/Places";
import { getDistrict } from "../../utils/getPlaces";

const DistrictPage: React.FC = () => {
    const navigate = useNavigate();
    const [district, setDistrict] = React.useState<District>();
    const [loading, setLoading] = React.useState(false);

    const { district_id } = useParams();

    useEffect(() => {
        const getData = async () => {
            if (!district_id) {
                return;
            }
            try {
                setLoading(true);
                const district = await getDistrict(district_id);
                setLoading(false);
                if (district) {
                    document.title = `${district.name} | nextbus`;
                    setDistrict(district);
                }
            } catch (error) {
                console.log("uh oh", error);
                navigate("/404", { replace: true });
            }
        };

        getData();
    }, [district_id]);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && district && (
                <>
                    <span className="mb-5 text-4xl font-bold">
                        Places in {district.name}
                    </span>
                    <div className="flex flex-col w-full gap-4">
                        <div className="flex flex-col items-center w-full mt-4">
                            {!district ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No District found.
                                </span>
                            ) : (
                                <div className="gap-4 mb-8 columns-2 sm:columns-3 md:columns-4 lg:columns-5">
                                    {district.localities?.map((locality) => (
                                        <div
                                            key={locality.id}
                                            className="flex flex-col mb-2 cursor-pointer break-inside-avoid"
                                            onClick={() =>
                                                navigate(
                                                    `/locality/${locality.id}`
                                                )
                                            }>
                                            <span className="underline text-link">
                                                {locality.name}
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

export default DistrictPage;
