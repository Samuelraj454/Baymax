import React from 'react';
import './Orb.css';

const Orb = ({ state = 'idle', volume = 0 }) => {
  // Map states to safe CSS classes
  const validStates = ['idle', 'activated', 'listening', 'processing', 'speaking', 'error'];
  const currentState = validStates.includes(state) ? state : 'idle';

  return (
    <div className={`orb-container state-${currentState}`}>
      <div className="core-indicator">
        {/* Core is styled entirely via CSS pseudo-elements for clean DOM */}
      </div>
      <div className="orb-status">
        {currentState === 'idle' ? 'Ready' : currentState}
      </div>
    </div>
  );
};

export default Orb;
