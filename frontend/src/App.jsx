import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import TabSelector from './components/TabSelector';
import TextPanel from './components/TextPanel';
import ImagePanel from './components/ImagePanel';
import VideoPanel from './components/VideoPanel';
import AudioPanel from './components/AudioPanel';

const App = () => {
  return (
    <Router>
      <div>
        <TabSelector />
        <Routes>
          <Route path="/text" element={<TextPanel />} />
          <Route path="/image" element={<ImagePanel />} />
          <Route path="/video" element={<VideoPanel />} />
          <Route path="/audio" element={<AudioPanel />} />
          <Route path="/" element={<TextPanel />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;