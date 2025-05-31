import React from 'react';

const DashedArrow = ({
  x1 = 0,
  y1 = 0,
  x2 = 200,
  y2 = 0,
  stroke = 'black',
  strokeWidth = 2,
  dashArray = '5,5',
  markerId = 'arrowhead',
}) => (
  <svg
    width={Math.abs(x2 - x1) + strokeWidth * 4}
    height={Math.abs(y2 - y1) + strokeWidth * 4}
    style={{ overflow: 'visible' }}
  >
    <defs>
      <marker
        id={markerId}
        markerWidth="10"
        markerHeight="7"
        refX="10"
        refY="3.5"
        orient="auto"
      >
        <polygon points="0 0, 10 3.5, 0 7" fill={stroke} />
      </marker>
    </defs>
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeDasharray={dashArray}
      markerEnd={`url(#${markerId})`}
    />
  </svg>
);

export default DashedArrow;
