import React, { useEffect } from "react";

const Data: React.FC = () => {
    useEffect(() => {
        document.title = "Data Sources | nextbus";
    }, []);
    return (
        <div className="flex flex-col max-w-3xl gap-5 p-6 mx-auto">
            <span className="text-4xl font-bold">Data Sources</span>
            <span>
                <strong>Last updated:</strong> October 2nd, 2025
            </span>

            <span>I use lots of open data to make nextbus possible.</span>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Bus Data</span>
                <ul className="list-disc list-inside">
                    <li>
                        All live bus data is provided by{" "}
                        <strong>
                            <a
                                href="https://bustimes.org"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                bustimes.org
                            </a>
                        </strong>
                        , through the use of their free{" "}
                        <strong>
                            <a
                                href="https://bustimes.org/api"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                API
                            </a>
                        </strong>
                        .
                    </li>
                    <li>
                        <strong>
                            <a
                                href="https://beta-naptan.dft.gov.uk/download/nptg"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                NPTG (National Public Transport Gazetter)
                            </a>
                        </strong>{" "}
                        for places.
                    </li>
                    <li>
                        <strong>
                            <a
                                href="https://beta-naptan.dft.gov.uk/download"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                NaPTAN (National Public Transport Access Nodes)
                            </a>
                        </strong>{" "}
                        for stop data.
                    </li>
                    <li>
                        <strong>
                            <a
                                href="https://data.bus-data.dft.gov.uk/"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                BODS (Bus Open Data Service)
                            </a>
                        </strong>{" "}
                        for timetables and routes.
                    </li>
                </ul>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Train Data</span>
                <ul className="list-disc list-inside">
                    <li>
                        All train data is provided by{" "}
                        <strong>
                            <a
                                href="https://www.realtimetrains.co.uk/"
                                className="underline text-link"
                                target="_blank"
                                rel="noopener noreferrer">
                                realtimetrains.co.uk
                            </a>
                        </strong>
                        , through the use of their free API.
                    </li>
                </ul>
            </div>
        </div>
    );
};

export default Data;
