import React from 'react';
import TopBar from '../shared/TopBar';
import NavBar from '../shared/NavBar';
import Footer from '../shared/Footer';
import Chatbot from '../shared/Chatbot';
import './Layout.css';

const Layout = ({ children }) => {
  return (
    <div className="wrapper">
      <TopBar />
      <NavBar />
      {children}
      <Footer />
      <Chatbot />
    </div>
  );
};

export default Layout;

