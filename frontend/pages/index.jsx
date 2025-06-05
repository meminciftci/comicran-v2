import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  addUEs,
  removeUEs,
  listUEs,
  handover,
  migrate,
  getAssignments,
  getLoads,
  getVBBUs,
} from "./api/api.js";
import UEview from "./UEview.jsx";
import Vbbuview from "./Vbbuview.jsx";
import NewVbbuView from "./newVbbuView.jsx";
import DummyVbbuView from "./dummyVbbuview.jsx";

function App() {
  const [ueStates, setUEStates] = useState({});
  const [uePositions, setUEPositions] = useState({});
  const antennaRef = useRef(null);
  const vbbuRef = useRef(null);
  const newVbbuRef = useRef(null);

  const [antennaPos, setAntennaPos] = useState(null);
  const [vbbuPos, setVbbuPos] = useState(null);
  const [newVbbuPos, setNewVbbuPos] = useState(null);

  const [assignments, setAssign] = useState({});
  const [loads, setLoads] = useState({});
  const [vbbus, setVBBUs] = useState({});
  const [handoverUE, setHandoverUE] = useState("1");
  const [sourceVBBU, setSourceVBBU] = useState("vbbu1");
  const [targetVBBU, setTargetVBBU] = useState("vbbu1");
  const [handoverTarget, setHandoverTarget] = useState("vbbu1");
  const [showAssignments, setShowAssignments] = useState(false);

  const [dataUpdateCount, setDataUpdateCount] = useState(0);
  const assignmentRef = useRef();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (assignmentRef.current && !assignmentRef.current.contains(e.target)) {
        setShowAssignments(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  const triggerUpdate = () => {
    setDataUpdateCount(dataUpdateCount + 1);
  };

  const handleAddUEs = async (uids, onConnect) => {
    const res = onConnect ? await addUEs(uids) : await removeUEs(uids);
    if (res.status === "ok") {
      listUEs().then(setUEStates);
    }
    getLoads().then(setLoads);
    getVBBUs().then(setVBBUs);
    getAssignments().then(setAssign);
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
    getAssignments().then(setAssign);
    const intervalId = setInterval(() => {
      getLoads().then(setLoads);
      getVBBUs().then(setVBBUs);
      getAssignments().then(setAssign);
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
    if (newVbbuRef.current) {
      const rect = newVbbuRef.current.getBoundingClientRect();
      setNewVbbuPos({
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
    setTimeout(updatePositions, 100);
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

        {/* Antenna → newVbbuView */}
        {antennaPos && newVbbuPos && (
          <line
            x1={antennaPos.x}
            y1={antennaPos.y}
            x2={newVbbuPos.x}
            y2={newVbbuPos.y}
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
                  console.log("loads", loads);
                  console.log("assignments", assignments);
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
            <div className="flex flex-col items-center gap-4 bg-gray-600 p-6 w-96 ">
              <div ref={newVbbuRef}>
                <NewVbbuView vbbus={vbbus} triggerUpdate={triggerUpdate} />
              </div>
              <div className="text-white text-2xl text-end w-full">
                Physical Node 2
              </div>
            </div>
          </div>
        </div>
        <div className="px-10 ml-32 flex flex-col gap-12">
          <div className="flex gap-5">
            {/* MIGRATE */}
            <div className="flex items-center gap-4 border-2 p-2 rounded-md">
              <div className="">
                <p className="text-gray-500">Source vBBU</p>
                {/* Source vBBU */}
                <select
                  className="border p-2 rounded-md w-40"
                  onChange={(e) => setSourceVBBU(e.target.value)}
                >
                  {vbbus?.data &&
                    Object.entries(vbbus.data).map(([key]) => (
                      <option key={key} value={key}>
                        {key}
                      </option>
                    ))}
                </select>
              </div>

              {/* Target vBBU (select all) */}
              <div>
                <p className="text-gray-500">Target vBBU</p>
                <select
                  className="border p-2 rounded-md w-40"
                  onChange={(e) => setTargetVBBU(e.target.value)}
                >
                  <option value="" disabled hidden>
                    Target vBBU
                  </option>
                  {vbbus?.data &&
                    Object.entries(vbbus.data).map(([key]) => (
                      <option key={key} value={key}>
                        {key}
                      </option>
                    ))}
                </select>
              </div>

              <button
                className="w-48 bg-blue-500 text-white p-2 text-xl font-bold rounded-3xl hover:bg-blue-900"
                onClick={() => {
                  console.log("migrate", sourceVBBU, targetVBBU);
                  if (targetVBBU && sourceVBBU) migrate(sourceVBBU, targetVBBU);
                }}
              >
                Migrate
              </button>
            </div>

            {/* HANDOVER */}
            <div className="flex items-center gap-4 border-2 p-2 rounded-md ">
              {/* Select Active UE */}

              <div>
                <p className="text-gray-500">Active UEs</p>
                <select
                  className="border p-2 rounded-md w-40"
                  onChange={(e) => setHandoverUE(e.target.value)}
                >
                  <option value="" disabled hidden>
                    Active UEs
                  </option>
                  {ueStates?.data &&
                    Object.entries(ueStates.data)
                      .filter(([_, state]) => state === "connected")
                      .map(([id]) => (
                        <option key={id} value={id}>
                          UE{id}
                        </option>
                      ))}
                </select>
              </div>

              {/* Select Target vBBU */}
              <div>
                <p className="text-gray-500">Target vBBU</p>
                <select
                  className="border p-2 rounded-md w-40"
                  onChange={(e) => setHandoverTarget(e.target.value)}
                >
                  <option value="" disabled hidden>
                    Target vBBU
                  </option>
                  {vbbus?.data &&
                    Object.entries(vbbus.data).map(([key]) => (
                      <option key={key} value={key}>
                        {key}
                      </option>
                    ))}
                </select>
              </div>

              <button
                className="w-48 bg-blue-500 text-white p-2 text-xl font-bold rounded-3xl hover:bg-blue-900"
                onClick={() => {
                  const new_ue = `UE${handoverUE}`;
                  console.log(handoverUE, new_ue, handoverTarget);
                  if (handoverUE && handoverTarget) {
                    handover(new_ue, handoverTarget);
                  }
                }}
              >
                Handover
              </button>
            </div>
          </div>
        </div>
      </div>
      <div
        ref={assignmentRef}
        className="absolute top-4 left-3/5 transform -translate-x-1/2 z-50"
      >
        <div className="relative inline-block">
          <button
            onClick={() => setShowAssignments((prev) => !prev)}
            className="bg-blue-500 text-white text-xl px-4 py-2 rounded-3xl shadow hover:bg-blue-700"
          >
            Show Assignments
          </button>

          {showAssignments && (
            <div className="absolute mt-2 bg-white border rounded shadow-lg max-h-64 overflow-auto w-64">
              {assignments?.data &&
                Object.entries(assignments.data)
                  .filter(
                    ([ue]) =>
                      ueStates?.data?.[ue.replace("UE", "")] === "connected"
                  )
                  .map(([ue, info]) => {
                    const ip = info.vbbu_ip;
                    let vbbuName = "Unknown";
                    if (ip.endsWith("201")) vbbuName = "vbbu1";
                    else if (ip.endsWith("202")) vbbuName = "vbbu1-prime";

                    return (
                      <div key={ue} className="px-4 py-2 hover:bg-gray-100">
                        <strong>{ue}</strong> → {vbbuName}
                      </div>
                    );
                  })}
            </div>
          )}
        </div>
      </div>

      <div className="absolute top-4 left-2/5 transform -translate-x-1/2 z-50">
        <div className="relative inline-block text-center">
          <p className="font-bold text-2xl ">HOMIC-RAN</p>
          <p>Handover-based Migration in Cloud-RAN</p>
        </div>
      </div>
    </div>
  );
}

export default App;
