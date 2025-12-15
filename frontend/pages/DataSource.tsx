import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { DetailedDataSource } from "../models/DataSource";
import { getDataSource } from "../utils/getSources";
import clsx from "clsx";

const DataSourcePage: React.FC = () => {
    const navigate = useNavigate();
    const [dataSource, setDataSource] = React.useState<DetailedDataSource>();
    const [loading, setLoading] = React.useState(false);
    const { source_id } = useParams();

    useEffect(() => {
        const getData = async () => {
            if (!source_id) {
                return;
            }
            try {
                setLoading(true);
                const ds = await getDataSource(Number(source_id));
                setLoading(false);
                if (ds) {
                    document.title = `${ds.name} | nextbus`;
                    setDataSource(ds);
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
            {!loading && dataSource && (
                <>
                    <span className="mb-5 text-4xl font-bold">
                        {dataSource.name}
                    </span>
                    <div className="w-full mt-4 overflow-x-auto max-h-[75vh] text-neutral-300/95">
                        {!dataSource ? (
                            <span className="w-full mb-5 text-sm text-center text-neutral-400">
                                No DataSource found.
                            </span>
                        ) : (
                            <table className="min-w-full mb-8 border rounded border-neutral-800">
                                <thead className="sticky top-0 z-10 bg-neutral-900">
                                    <tr>
                                        <th className="px-4 py-2 text-left border-b">
                                            service code
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            line
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            revision
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            start
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            end
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            modified
                                        </th>
                                        <th className="px-4 py-2 text-left border-b">
                                            journeys
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(
                                        dataSource.services ?? {}
                                    ).map(([serviceCode, lines]) =>
                                        Object.entries(lines).map(
                                            ([
                                                lineName,
                                                { service, timetables },
                                            ]) =>
                                                timetables &&
                                                timetables.length > 0 ? (
                                                    timetables.map(
                                                        (timetable, idx) => (
                                                            <tr
                                                                key={`${serviceCode}-${lineName}-${
                                                                    timetable.id ??
                                                                    idx
                                                                }`}
                                                                className={clsx(
                                                                    "cursor-pointer hover:bg-neutral-800 transition-colors",
                                                                    idx > 0
                                                                        ? "border-t-0"
                                                                        : "border-t border-neutral-700"
                                                                    // "border-b border-neutral-800"
                                                                )}
                                                                onClick={() =>
                                                                    navigate(
                                                                        `/buses/services/${service.id}`
                                                                    )
                                                                }>
                                                                <td
                                                                    className={clsx(
                                                                        "px-4 py-2 text-neutral-400 align-top",
                                                                        idx > 0
                                                                            ? "border-t-0 text-transparent select-none"
                                                                            : ""
                                                                    )}>
                                                                    {
                                                                        serviceCode
                                                                    }
                                                                </td>
                                                                <td className="px-4 py-2 align-top">
                                                                    {lineName}
                                                                </td>
                                                                <td className="px-4 py-2 align-top">
                                                                    {
                                                                        timetable.revision_number
                                                                    }
                                                                </td>
                                                                <td className="px-4 py-2 align-top">
                                                                    {new Date(
                                                                        timetable.start_date
                                                                    ).toLocaleDateString(
                                                                        "en-GB",
                                                                        {
                                                                            day: "numeric",
                                                                            month: "long",
                                                                            year: "numeric",
                                                                        }
                                                                    )}
                                                                </td>
                                                                <td className="px-4 py-2 align-top">
                                                                    {timetable.end_date
                                                                        ? new Date(
                                                                              timetable.end_date
                                                                          ).toLocaleDateString(
                                                                              "en-GB",
                                                                              {
                                                                                  day: "numeric",
                                                                                  month: "long",
                                                                                  year: "numeric",
                                                                              }
                                                                          )
                                                                        : "Ongoing"}
                                                                </td>
                                                                <td className="px-4 py-2 align-top text-nowrap">
                                                                    {timetable.modified_at
                                                                        ? new Date(
                                                                              timetable.modified_at
                                                                          ).toLocaleString(
                                                                              "en-GB",
                                                                              {
                                                                                  day: "numeric",
                                                                                  month: "numeric",
                                                                                  year: "numeric",
                                                                                  hour: "2-digit",
                                                                                  minute: "2-digit",
                                                                              }
                                                                          )
                                                                        : "N/A"}
                                                                </td>
                                                                <td className="px-4 py-2 align-top">
                                                                    {
                                                                        timetable.journey_count
                                                                    }
                                                                </td>
                                                            </tr>
                                                        )
                                                    )
                                                ) : (
                                                    <tr
                                                        key={`${serviceCode}-${lineName}-no-timetable`}
                                                        className="border-b cursor-pointer hover:bg-neutral-800 border-neutral-800"
                                                        onClick={() =>
                                                            navigate(
                                                                `/buses/services/${service.id}`
                                                            )
                                                        }>
                                                        <td className="px-4 py-2 text-gray-500">
                                                            {serviceCode}
                                                        </td>
                                                        <td className="px-4 py-2">
                                                            {lineName}
                                                        </td>
                                                        <td
                                                            className="px-4 py-2"
                                                            colSpan={2}>
                                                            No timetables
                                                        </td>
                                                        <td className="px-4 py-2 text-nowrap">
                                                            {service.last_modified
                                                                ? new Date(
                                                                      service.last_modified
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
                                                    </tr>
                                                )
                                        )
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default DataSourcePage;
