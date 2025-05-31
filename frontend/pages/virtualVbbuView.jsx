import React from "react";
import { removeUEs,
activateVBBU, deactivateVBBU, listUEs
} from "./api/api.js";

function VirtualVbbuView({ vbbus, triggerUpdate }) {
  const virtualVbbu = vbbus?.data?.vbbu3
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
  if (!virtualVbbu) {
    return(<></>)
  }
  const handleActivate = async() =>{
    console.log('now',virtualVbbu.is_active)
    const activeUEs = await listUEs();
    const connectedUEs = Object.entries(activeUEs.data)
    .filter(([_, state]) => state === "connected")
    .map(([id]) => Number(id));
    console.log(connectedUEs)
      if (virtualVbbu.is_active) {
        const res = await deactivateVBBU('vbbu3')


        console.log('deactivate virtual', virtualVbbu.is_active)
        // console.log('remove res', res1)
        triggerUpdate()
        return res
      }
      if (!virtualVbbu.is_active) {
        const res = await activateVBBU('vbbu3')
        
        console.log('activate virtual', virtualVbbu.is_active)
        triggerUpdate()
        return res
      }
    }
  return (
    
  
   
      <div className="flex items-center gap-4 bg-gray-300 p-4">
        {/* Usage Bar Container */}
        <div className="w-48 h-32 border border-black relative bg-white overflow-hidden rounded-md shadow-sm">
          {/* Fill based on usage */}
          <div
            className={`absolute bottom-0 left-0 w-full ${backgroundColorNew(
              virtualVbbu.connections
            )}`}
            style={{
              // TODO: Change height
              height: `${typeof(virtualVbbu.connections) === typeof(0) ? virtualVbbu.connections*10 : 0}%`,
              transition: 'height 0.5s ease-in-out',
            }}
          >
            <div className="text-center w-full text-md font-semibold text-black -mt-1">
            {/* // TODO: Change virtualVbbu */}
              {
              
              typeof(virtualVbbu.connections) === typeof(0) ? virtualVbbu.connections*10 : 0 }%
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-2 items-center">

        
        {/* Label */}
        <span className="text-lg font-medium text-gray-800">
          VBBU1*
        </span>
        <button className="bg-blue-500 p-2 rounded-2xl text-white hover:bg-blue-600 w-22" onClick={()=>{
          handleActivate()
        }}>
          {virtualVbbu.is_active ? 'Deactivate' : 'Activate'}
        </button>
        </div>
      </div>



  );
}

export default VirtualVbbuView;
