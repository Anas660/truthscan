import React from 'react';

const TabSelector = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="tab-selector">
      {tabs.map((tab) => (
        <button
          key={tab}
          className={`tab-button ${activeTab === tab ? 'active' : ''}`}
          onClick={() => onTabChange(tab)}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};

export default TabSelector;