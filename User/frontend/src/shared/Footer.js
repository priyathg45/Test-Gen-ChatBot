import React from 'react';

const Footer = () => (
  <div className="footer">
    <div className="container">
      <div className="row">
        <div className="col-md-6 col-lg-3">
          <div className="footer-contact">
            <h2>Active Aluminium Windows Contact</h2>
            <p>
              <i className="fa fa-map-marker-alt" />
              123 Industrial Estate, Production Facility, Colombo.
            </p>
            <p>
              <i className="fa fa-phone-alt" />
              +94 11 234 5678
            </p>
            <p>
              <i className="fa fa-envelope" />
              support@activealuminium.com
            </p>
            <div className="footer-social">
              <a href="#twitter">
                <i className="fab fa-twitter" />
              </a>
              <a href="#facebook">
                <i className="fab fa-facebook-f" />
              </a>
              <a href="#youtube">
                <i className="fab fa-youtube" />
              </a>
              <a href="#instagram">
                <i className="fab fa-instagram" />
              </a>
              <a href="#linkedin">
                <i className="fab fa-linkedin-in" />
              </a>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="footer-link">
            <h2>System Areas</h2>
            <a href="#dashboard">Production Dashboard</a>
            <a href="#library">Product Library</a>
            <a href="#assignments">Worker Assignments</a>
            <a href="#reporting">Reporting</a>
            <a href="#settings">Admin Settings</a>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="footer-link">
            <h2>Useful Links</h2>
            <a href="#help">Help &amp; Guides</a>
            <a href="#notes">Release Notes</a>
            <a href="#support">Contact Support</a>
            <a href="#status">Status</a>
            <a href="#privacy">Privacy</a>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="newsletter">
            <h2>Production Updates</h2>
            <p>
              The official production system for Active Aluminium Windows. Receive updates on new system
              capabilities and workflow improvements.
            </p>
            <div className="form">
              <input className="form-control" placeholder="Email here" />
              <button className="btn" type="button">
                Submit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div className="container footer-menu">
      <div className="f-menu">
        <a href="#terms">Terms of use</a>
        <a href="#policy">Privacy policy</a>
        <a href="#cookies">Cookies</a>
        <a href="#help-footer">Help</a>
        <a href="#faqs">FAQs</a>
      </div>
    </div>
    <div className="container copyright">
      <div className="row">
        <div className="col-md-6">
          <p>
            &copy; <a href="#aaw">Active Aluminium Windows</a>. © 2026 Active Aluminium Windows. All Rights
            Reserved.
          </p>
        </div>
        <div className="col-md-6" />
      </div>
    </div>
  </div>
);

export default Footer;

