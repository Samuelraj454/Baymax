import React from 'react';
import './Orb.css';

const Orb = ({ state = 'idle' }) => {
  return (
    <div className={`baymax-orb-container ${state}`}>
      <div className="orb-rings">
        <div className="ring ring-1"></div>
        <div className="ring ring-2"></div>
        <div className="ring ring-3"></div>
      </div>
      
      <div className="main-orb">
        <div className="orb-core"></div>
        <div className="orb-glow"></div>
        
        {state === 'processing' && (
          <div className="processing-ring"></div>
        )}
        
        {state === 'speaking' && (
          <div className="speaking-waves">
            <div className="wave wave-1"></div>
            <div className="wave wave-2"></div>
            <div className="wave wave-3"></div>
            <div className="wave wave-4"></div>
            <div className="wave wave-5"></div>
          </div>
        )}
      </div>
      
      {state === 'error' && (
        <div className="error-flash"></div>
      )}
    </div>
  );
};

export default Orb;
