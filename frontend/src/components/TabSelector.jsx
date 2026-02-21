const TABS = [
  { id: "text", label: "Text", icon: "📝", activeClass: "active-yellow" },
  { id: "image", label: "Image", icon: "🖼️", activeClass: "active-orange" },
  { id: "video", label: "Video", icon: "🎬", activeClass: "active-pink" },
  { id: "audio", label: "Audio", icon: "🎵", activeClass: "active-cyan" },
];

export default function TabSelector({ activeTab, setActiveTab }) {
  return (
    <div className="tab-selector">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? tab.activeClass : ""}`}
          onClick={() => setActiveTab(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}
