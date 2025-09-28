import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { AdminArea } from "../../models/Places";
import { getAdminArea } from "../../utils/getPlaces";

const AdminAreaPage: React.FC = () => {
    const navigate = useNavigate();
    const [admin_area, setadmin_area] = React.useState<AdminArea>();
    const [loading, setLoading] = React.useState(false);

    const { admin_area_id } = useParams();

    useEffect(() => {
        const getData = async () => {
            if (!admin_area_id) {
                return;
            }
            try {
                setLoading(true);
                const admin_area = await getAdminArea(admin_area_id);
                setLoading(false);
                if (admin_area) {
                    document.title = `${admin_area.name} | nextbus`;
                    setadmin_area(admin_area);
                }
            } catch (error) {
                console.log("uh oh", error);
                navigate("/404", { replace: true });
            }
        };

        getData();
    }, [admin_area_id]);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && admin_area && (
                <>
                    <span className="mb-5 text-4xl font-bold">
                        Places in {admin_area.name}
                    </span>
                    <div className="flex flex-col w-full gap-4">
                        <div className="flex flex-col items-center w-full mt-4">
                            {!admin_area ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No admin_area found.
                                </span>
                            ) : (
                                <div className="gap-4 mb-8 columns-2 md:columns-3 lg:columns-4">
                                    {admin_area.districts?.map((district) => (
                                        <div
                                            key={district.id}
                                            className="mb-2 cursor-pointer break-inside-avoid"
                                            onClick={() => {
                                                navigate(
                                                    `/district/${district.id}`
                                                );
                                            }}>
                                            <span className="underline text-sky-500">
                                                {district.name}
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

export default AdminAreaPage;
