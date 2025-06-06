import React from "react";
import { removeUEs, activateVBBU, deactivateVBBU, listUEs } from "./api/api.js";

function VirtualVbbuView({ vbbus, triggerUpdate }) {
  const newVbbu = vbbus?.data?.["vbbu1-prime"];
  const backgroundColorNew = (connections) => {
    if (newVbbu.cpu >= 70) {
      return "bg-red-500";
    } else if (newVbbu.cpu >= 50) {
      return "bg-amber-500";
    } else {
      return "bg-green-500";
    }
  };
  if (!newVbbu) {
    return <></>;
  }
  const handleActivate = async () => {
    console.log("now", newVbbu.is_active);
    const activeUEs = await listUEs();
    const connectedUEs = Object.entries(activeUEs.data)
      .filter(([_, state]) => state === "connected")
      .map(([id]) => Number(id));
    console.log(connectedUEs);
    if (newVbbu.is_active) {
      const res = await deactivateVBBU("vbbu1-prime");

      console.log("deactivate virtual", newVbbu.is_active);
      // console.log('remove res', res1)
      triggerUpdate();
      return res;
    }
    if (!newVbbu.is_active) {
      const res = await activateVBBU("vbbu1-prime");

      console.log("activate virtual", newVbbu.is_active);
      triggerUpdate();
      return res;
    }
  };
  return (
    <div className="flex items-center gap-4 bg-gray-300 p-4">
      {/* Usage Bar Container */}
      <div
        className="w-48 h-48 border border-black relative bg-white overflow-hidden rounded-md shadow-sm"
        style={{
          opacity: newVbbu.is_active ? 1 : 0.3,
        }}
      >
        {/* Fill based on usage */}
        <div
          className={`absolute bottom-0 left-0 w-full ${backgroundColorNew()}`}
          style={{
            // TODO: Change height
            height: `${
              typeof newVbbu.connections === typeof 0 ? newVbbu.cpu : 0
            }%`,
            transition: "height 0.5s ease-in-out",
            display: newVbbu.is_active ? "block" : "none",
          }}
        >
          <div className="text-center w-full text-md font-semibold text-black -mt-1">
            {/* // TODO: Change virtualVbbu */}
            {typeof newVbbu.connections === typeof 0 ? newVbbu.cpu : 0}%
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2 items-center">
        {/* Label */}
        <span
          className="text-lg font-medium text-gray-800"
          style={{ opacity: newVbbu.is_active ? 1 : 0.3 }}
        >
          vBBU1*
        </span>
        <button
          className="bg-blue-500 p-2 rounded-2xl text-white hover:bg-blue-600 w-22"
          onClick={() => {
            handleActivate();
          }}
        >
          {newVbbu.is_active ? "Deactivate" : "Activate"}
        </button>
      </div>
    </div>
  );
}

export default VirtualVbbuView;
