import React, { useState } from "react";

function DummyVbbuView() {
  const [isActive, setIsActive] = useState(true);

  return (
    <>
      <div className="flex items-center gap-4 bg-gray-300 p-4 mt-1">
        {/* Usage Bar Container */}
        <div
          className="w-48 h-32 border border-black relative bg-white overflow-hidden rounded-md shadow-sm"
          style={{
            opacity: isActive ? 1 : 0.3,
          }}
        >
          <div
            className="absolute bottom-0 left-0 w-full bg-amber-500"
            style={{
              transition: "height 0.5s ease-in-out",
              height: isActive ? 76 : 0,
            }}
          >
            <div className="text-center w-full text-md font-semibold text-black mb-1">
              60%
            </div>
          </div>
        </div>

        {/* Label and Button */}
        <div className="flex flex-col gap-2 items-center">
          <span
            className="text-lg font-medium text-gray-800"
            style={{ opacity: isActive ? 1 : 0.3 }}
          >
            vBBU2
          </span>

          {/* Button stays fully opaque */}
          <button
            className="bg-blue-500 p-2 rounded-2xl text-white hover:bg-blue-600 w-22"
            onClick={() => setIsActive(!isActive)}
          >
            {isActive ? "Deactivate" : "Activate"}
          </button>
        </div>
      </div>
    </>
  );
}

export default DummyVbbuView;
