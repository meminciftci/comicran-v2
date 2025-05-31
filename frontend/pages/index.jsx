import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  addUEs,
  removeUEs,
  listUEs,
  handover,
  migrate,
  activateVBBU,
  deactivateVBBU,
  getAssignments,
  getLoads,
  getVBBUs,
} from "./api/api.js";
import UEview from "./UEview.jsx";
import Vbbuview from "./Vbbuview.jsx";
import VirtualVbbuView from "./virtualVbbuView.jsx";
import DummyVbbuView from "./dummyVbbuview.jsx";

function App() {
  const [ueStates, setUEStates] = useState({});
  const [uePositions, setUEPositions] = useState({});
  const antennaRef = useRef(null);
  const vbbuRef = useRef(null);
  const virtualVbbuRef = useRef(null);

  const [antennaPos, setAntennaPos] = useState(null);
  const [vbbuPos, setVbbuPos] = useState(null);
  const [virtualVbbuPos, setVirtualVbbuPos] = useState(null);

  const [assignments, setAssign] = useState({});
  const [loads, setLoads] = useState({});
  const [vbbus, setVBBUs] = useState({});
  const [inputUEs, setInputUEs] = useState("");
  const [handoverUE, setHandoverUE] = useState("");
  const [targetVBBU, setTargetVBBU] = useState("");
  const [showHandoverDropdown, setShowHandoverDropdown] = useState(false);
  
  const [dataUpdateCount, setDataUpdateCount] = useState(0)

  const triggerUpdate = () => {setDataUpdateCount(dataUpdateCount+1)}


  const handleAddUEs = async (uids, onConnect) => {
    const res = onConnect ? await addUEs(uids) : await removeUEs(uids);
    if (res.status === "ok") {
      listUEs().then(setUEStates);
    }
    getLoads().then(setLoads);
    getVBBUs().then(setVBBUs);
  };

  useEffect(() => {
    listUEs().then(setUEStates);
    getAssignments().then(setAssign);
    getLoads().then(setLoads);
    getVBBUs().then(setVBBUs);
  }, [dataUpdateCount]);

  useEffect(() => {
    getLoads().then(setLoads);
    getVBBUs().then(setVBBUs);
    const intervalId = setInterval(() => {
      getLoads().then(setLoads);
      getVBBUs().then(setVBBUs);
    }, 1000);
    return () => clearInterval(intervalId);
  }, []);

  const reportUEPosition = useCallback((name, pos) => {
    setUEPositions((prev) => ({ ...prev, [name]: pos }));
  }, []);
  const updatePositions = () => {
    if (antennaRef.current) {
      const antennaRect = antennaRef.current.getBoundingClientRect();
      setAntennaPos({
        x: antennaRect.left + (antennaRect.right - antennaRect.left) / 2,
        y: antennaRect.bottom + (antennaRect.top - antennaRect.bottom) / 2,
      });
    }
    if (vbbuRef.current) {
      const vbbuRect = vbbuRef.current.getBoundingClientRect();
      setVbbuPos({
        x: vbbuRect.left,
        y: vbbuRect.bottom + (vbbuRect.top - vbbuRect.bottom) / 2,
      });
    }
    if (virtualVbbuRef.current) {
      const rect = virtualVbbuRef.current.getBoundingClientRect();
      setVirtualVbbuPos({
        x: rect.left,
        y: rect.top + rect.height / 2,
      });
    }
  };
  useEffect(() => {
    updatePositions();
    window.addEventListener("resize", updatePositions);
    window.addEventListener("scroll", updatePositions);
    return () => {
      window.removeEventListener("resize", updatePositions);
      window.removeEventListener("scroll", updatePositions);
    };
  }, []);
  useEffect(() => {
    setTimeout(updatePositions, 100); // Let layout settle
  }, []);
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest(".handover-wrapper")) {
        setShowHandoverDropdown(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  return (
    <div className="h-[100vh]">
      <svg
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="black" />
          </marker>
        </defs>

        {/* UE Arrows */}
        {antennaPos &&
          Object.entries(uePositions).map(([name, { x, y, isActive }]) => (
            <line
              key={name}
              x1={x + 48}
              y1={y}
              x2={antennaPos.x}
              y2={antennaPos.y}
              stroke={isActive ? "#0d0" : "#000"}
              strokeWidth="2"
              strokeDasharray="6,4"
              markerEnd="url(#arrowhead)"
            />
          ))}

        {/* Antenna → Vbbuview */}
        {antennaPos && vbbuPos && (
          <line
            x1={antennaPos.x}
            y1={antennaPos.y}
            x2={vbbuPos.x}
            y2={vbbuPos.y}
            stroke="black"
            strokeWidth="3"
            markerEnd="url(#arrowhead)"
          />
        )}

        {/* Antenna → VirtualVbbuView */}
        {antennaPos && virtualVbbuPos && (
          <line
            x1={antennaPos.x}
            y1={antennaPos.y}
            x2={virtualVbbuPos.x}
            y2={virtualVbbuPos.y}
            stroke="black"
            strokeWidth="3"
            markerEnd="url(#arrowhead)"
          />
        )}
      </svg>

      <div className="grid grid-cols-2">
        <div className="">
          {ueStates?.data &&
            Object.entries(ueStates.data).map(([id, state]) => (
              <button
                key={id}
                className="flex"
                onClick={() => {
                  handleAddUEs([Number(id)], state === "disconnected");
                  console.log("ue", ueStates?.data);
                  console.log("vbbus", vbbus?.data);
                  console.log('loads',loads)
                }}
              >
                <UEview
                  name={`UE${id}`}
                  isActive={state === "connected"}
                  reportPosition={reportUEPosition}
                />
              </button>
            ))}
        </div>

        <div className="grid grid-cols-2">
          <div className="flex items-center justify-center">
            <img
              ref={antennaRef}
              className="w-32 h-32"
              src="/antenna.gif"
              alt="antenna"
              onLoad={updatePositions}
            />
          </div>
          <div className="flex flex-col items-center justify-center gap-10">
            <div className="flex flex-col items-center gap-4 bg-gray-600 p-6 w-96">
              <div ref={vbbuRef}>
                <Vbbuview vbbu={vbbus?.data?.vbbu1} />
              </div>
              <DummyVbbuView />

              <div className="text-white text-2xl text-end w-full">
                Physical Node 1
              </div>
            </div>
            <div className="flex flex-col items-center gap-4 bg-gray-600 p-6 w-96 h-64">
              <div ref={virtualVbbuRef}>
                
              <VirtualVbbuView vbbus={vbbus} triggerUpdate={triggerUpdate} />
              </div>
              <div className="text-white text-2xl text-end w-full">
                Physical Node 2
              </div>
            </div>
          </div>
        </div>
        <div className=" px-10 ml-32 flex items-center justify-center gap-12">
          <button
            className="h-18 w-64 bg-blue-500 text-white p-4 text-3xl font-bold rounded-3xl hover:bg-blue-900"
            onClick={() => {
              migrate("vbbu1");
            }}
          >
            Migrate
          </button>
          <div className="relative handover-wrapper">
            <button
              className="h-18 w-64 bg-blue-500 text-white p-4 text-3xl font-bold rounded-3xl hover:bg-blue-900"
              onClick={() => setShowHandoverDropdown((prev) => !prev)}
            >
              Handover
            </button>

            {showHandoverDropdown && (
              <div className="absolute bottom-[100%] mb-2 w-64 bg-white border border-gray-300 rounded shadow z-50 max-h-64 overflow-auto">
                {ueStates?.data &&
                  Object.entries(ueStates.data)
                    .filter(([_, state]) => state === "connected")
                    .map(([id]) => (
                      <button
                        key={id}
                        className="w-full text-left px-4 py-2 hover:bg-gray-100"
                        onClick={() => {
                          handover(id, 'vbbu3'); // You must set `targetVBBU` somehow
                          setShowHandoverDropdown(false);
                        }}
                      >
                        UE{id}
                      </button>
                    ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
