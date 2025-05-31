import React from "react";
import {
  addUEs, removeUEs, listUEs,
  handover, migrate, activateVBBU, deactivateVBBU,
  getAssignments, getLoads, getVBBUs
} from "./api/api.js";

function Vbbuview({ vbbu }) {
  
  const backgroundColorNew = (connections) => {
    const load = connections / 10;
    if (load >= 0.7) {
      return "bg-red-500";
    } else if (load >= 0.5) {
      return "bg-amber-500";
    } else {
      return "bg-green-500";
    }
  };
  if(!vbbu){
    return null
  }
  const handleActivate = async() =>{
    if (vbbu.is_active) {
      const res = await deactivateVBBU('vbbu1')
      console.log('deactivate res', vbbu.is_active)
      return res
    }
    if (!vbbu.is_active) {
      const res = await activateVBBU('vbbu1')
      console.log('activate res', vbbu.is_active)
      return res
    }
  }
  return (
    <>
      <div className="flex items-center gap-4 bg-gray-300 p-4 mt-1">
        {/* Usage Bar Container */}
        <div className="w-48 h-48 border border-black relative bg-white overflow-hidden rounded-md shadow-sm">
          {/* Fill based on usage */}
          <div
            className={`absolute bottom-0 left-0 w-full ${backgroundColorNew(
              vbbu.connections
            )}`}
            style={{
              // TODO: Change height
              height: `${vbbu.connections*10}%`,
              transition: 'height 0.5s ease-in-out',
            }}
          >
            <div className="text-center w-full text-md font-semibold text-black mb-1">
            {/* // TODO: Change value */}
              {vbbu.connections*10}%
            </div>
          </div>
        </div>

        {/* Label */}
        <div className="flex flex-col gap-2 items-center">

        <span className="text-lg font-medium text-gray-800">
          vBBU1
        </span>
        <button className="bg-blue-500 p-2 rounded-2xl text-white hover:bg-blue-600 w-22" onClick={()=>{
          handleActivate()
        }}>
          {vbbu.is_active ? 'Deactivate' : 'Activate'}
        </button>
        </div>
      </div>
</>

  );
}

export default Vbbuview;
