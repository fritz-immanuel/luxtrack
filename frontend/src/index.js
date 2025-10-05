if (typeof window !== 'undefined' && !window.$RefreshSig$) {
  window.$RefreshSig$ = function() { return function(type) { return type; }; };
  window.$RefreshReg$ = function() {};
}

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
