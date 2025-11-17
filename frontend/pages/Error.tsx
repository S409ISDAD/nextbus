import React from "react";

const Error: React.FC = () => (
    <div className="flex flex-col items-center justify-center gap-4 text-center py-50">
        <h1 className="text-6xl font-bold">
            Sorry, <span className="text-primary-500">Not in Service</span>
        </h1>
        <p className="text-lg">Whoops, something went wrong.</p>
        <button
            className="p-2 px-10 mt-2 font-semibold text-white transition-all cursor-pointer bg-primary rounded-xl hover:bg-primary-700"
            onClick={() => {
                window.location.reload();
            }}>
            Retry
        </button>
        <button
            className="p-2 px-10 mt-2 font-semibold text-white transition-all cursor-pointer bg-primary rounded-xl hover:bg-primary-700"
            onClick={() => {
                window.location.href = `/`;
            }}>
            Go Home
        </button>
    </div>
);

export default Error;
