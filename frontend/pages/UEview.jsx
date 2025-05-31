import React, { useEffect, useRef } from "react";

function UEview({ name, isActive, reportPosition }) {
  const buttonRef = useRef(null);

  useEffect(() => {
    const updateCoords = () => {
      if (buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;
        reportPosition(name, { x, y, isActive });
      }
    };

    updateCoords();
    window.addEventListener("resize", updateCoords);
    window.addEventListener("scroll", updateCoords);
    return () => {
      window.removeEventListener("resize", updateCoords);
      window.removeEventListener("scroll", updateCoords);
    };
  }, [name, isActive, reportPosition]);

  return (
    <div className="flex items-center p-3">
      <button
        ref={buttonRef}
        className={`flex w-20 h-15 items-center justify-center font-bold text-3xl border-2 rounded-xl ${
          isActive ? "bg-[#0d0]" : ""
        }`}
      >
        {name}
      </button>
    </div>
  );
}

export default UEview;
