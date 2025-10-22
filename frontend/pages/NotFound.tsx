import React from "react";

const NotFound: React.FC = () => (
    <div className="flex flex-col items-center justify-center gap-4 text-center py-50">
        <h1 className="text-6xl font-bold">
            404 to <span className="text-primary-500">Nowhere</span>
        </h1>
        <p className="text-lg">Sorry, but this page will never depart.</p>
        <button
            className="p-2 px-10 mt-2 font-semibold text-text-dark transition-all bg-primary cursor-pointer rounded-xl hover:bg-primary-700"
            onClick={() => {
                window.location.href = `/`;
            }}>
            Go Home
        </button>
    </div>
);

export default NotFound;
