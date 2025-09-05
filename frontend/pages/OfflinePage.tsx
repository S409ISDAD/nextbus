import React from "react";

const OfflinePage: React.FC = () => (
    <div className="flex flex-col items-center justify-center gap-4 text-center py-50">
        <h1 className="text-6xl font-bold">
            You are <span className="text-blue-500">offline</span>
        </h1>
        <p className="text-lg">
            Sorry, but nextbus could not be loaded. make sure you are connected
            to internet and try again.
        </p>
        <button
            className="p-2 px-10 mt-2 font-semibold text-white transition-all bg-blue-600 cursor-pointer rounded-xl hover:bg-blue-700"
            onClick={() => {
                window.location.href = `/`;
            }}>
            Try Again
        </button>
    </div>
);

export default OfflinePage;
