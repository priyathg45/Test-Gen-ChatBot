import React from 'react';

const TopBar = () => (
  <div className="top-bar">
    <div className="container-fluid">
      <div className="row align-items-center">
        <div className="col-lg-3 col-md-12">
          <div className="logo">
            <a href="/">
              <h1>Active Aluminium Windows</h1>
            </a>
          </div>
        </div>
        <div className="col-lg-9 col-md-7 d-none d-lg-block">
          <div className="row justify-content-center">
            <div className="col-auto">
              <div className="top-bar-item">
                <div className="top-bar-icon">
                  <i className="flaticon-calendar" />
                </div>
                <div className="top-bar-text">
                  <h3>Opening Hours</h3>
                  <p>Mon - Fri, 8:00 - 17:00</p>
                </div>
              </div>
            </div>
            <div className="col-auto">
              <div className="top-bar-item">
                <div className="top-bar-icon">
                  <i className="flaticon-call" />
                </div>
                <div className="top-bar-text">
                  <h3>Call Us</h3>
                  <p>+012 345 6789</p>
                </div>
              </div>
            </div>
            <div className="col-auto">
              <div className="top-bar-item">
                <div className="top-bar-icon">
                  <i className="flaticon-send-mail" />
                </div>
                <div className="top-bar-text">
                  <h3>Email Us</h3>
                  <p>info@activealuminumwindows.com</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default TopBar;

