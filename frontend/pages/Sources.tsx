import React, { useEffect } from "react";
import { useNavigate } from "react-router";
import type { SimpleDataSource } from "../models/DataSource";
import { getSources } from "../utils/getSources";

const SourcesPage: React.FC = () => {
    const navigate = useNavigate();
    const [dataSources, setDataSources] = React.useState<SimpleDataSource[]>();
    const [loading, setLoading] = React.useState(false);

    useEffect(() => {
        const getData = async () => {
            try {
                setLoading(true);
                const ds = await getSources();
                setLoading(false);
                if (ds) {
                    document.title = `Sources | nextbus`;
                    setDataSources(ds);
                }
            } catch (error) {
                console.log("uh oh", error);
                navigate("/404", { replace: true });
            }
        };

        getData();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 px-1 pb-0 md:px-8">
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && dataSources && (
                <>
                    <span className="mb-5 text-4xl font-bold">
                        Data Sources
                    </span>
                    <div className="w-full mt-4 overflow-x-auto">
                        {!dataSources ? (
                            <span className="w-full mb-5 text-sm text-center text-neutral-400">
                                No DataSources found.
                            </span>
                        ) : (
                            <table className="min-w-full mb-8 border rounded border-neutral-800">
                                <thead>
                                    <tr>
                                        <th className="px-4 py-2 text-left border-b">
                                            ID
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            Name
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            URL/BODS
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            Modified
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            Services
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            Timetables
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {dataSources.map((source) => (
                                        <React.Fragment key={source.id}>
                                            <tr className="border-t border-neutral-700 bg-neutral-900">
                                                <td className="px-4 py-2 text-gray-500">
                                                    {source.id}
                                                </td>
                                                <td
                                                    className="px-4 py-2 font-semibold cursor-pointer"
                                                    onClick={() =>
                                                        navigate(
                                                            `/sources/${source.id}`
                                                        )
                                                    }>
                                                    {source.name}
                                                </td>
                                                <td className="px-4 py-2 text-gray-500">
                                                    —
                                                </td>
                                                <td className="px-4 py-2 text-gray-500">
                                                    —
                                                </td>
                                                <td className="px-4 py-2">
                                                    {source.service_count}
                                                </td>
                                                <td className="px-4 py-2">
                                                    {source.timetable_count}
                                                </td>
                                            </tr>

                                            {/* Versions */}
                                            {source.versions.map((version) => (
                                                <tr
                                                    key={version.id}
                                                    className="transition border-t border-neutral-800 hover:bg-neutral-800">
                                                    <td className="px-4 py-2 pl-8 text-gray-500">
                                                        {version.id}
                                                    </td>
                                                    <td className="px-4 py-2 text-ellipsis">
                                                        {version.name}
                                                    </td>
                                                    <td
                                                        className="px-4 py-2 underline cursor-pointer text-link text-ellipsis"
                                                        onClick={() =>
                                                            window.open(
                                                                version.url ||
                                                                    (version.bods_id
                                                                        ? `https://data.bus-data.dft.gov.uk/timetable/dataset/${version.bods_id}/`
                                                                        : "N/A"),
                                                                "_blank",
                                                                "noreferrer"
                                                            )
                                                        }>
                                                        {version.url ||
                                                            (version.bods_id
                                                                ? `https://data.bus-data.dft.gov.uk/timetable/dataset/${version.bods_id}/`
                                                                : "N/A")}
                                                    </td>
                                                    <td className="px-4 py-2 text-ellipsis">
                                                        {version.last_modified
                                                            ? new Date(
                                                                  version.last_modified
                                                              ).toLocaleString(
                                                                  "en-GB",
                                                                  {
                                                                      day: "numeric",
                                                                      month: "long",
                                                                      year: "numeric",
                                                                      hour: "2-digit",
                                                                      minute: "2-digit",
                                                                      timeZoneName:
                                                                          "short",
                                                                  }
                                                              )
                                                            : "N/A"}
                                                    </td>
                                                    <td className="px-4 py-2 text-gray-500">
                                                        —
                                                    </td>
                                                    <td
                                                        className={`px-4 py-2 ${
                                                            !version.timetable_count
                                                                ? "text-gray-500"
                                                                : ""
                                                        }`}>
                                                        {version.timetable_count ||
                                                            "—"}
                                                    </td>
                                                </tr>
                                            ))}
                                        </React.Fragment>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default SourcesPage;
