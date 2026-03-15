import React from 'react';

const ContactPage = () => (
  <>
    <div className="page-header">
      <h2>Contact Us</h2>
    </div>
    <div className="contact">
      <div className="container">
        <div className="row">
          <div className="col-md-6">
            <div className="contact-info">
              <div className="contact-item">
                <i className="flaticon-address" />
                <div className="contact-text">
                  <h2>Head Office</h2>
                  <p>123 Industrial Estate, Production Facility, Colombo.</p>
                </div>
              </div>
              <div className="contact-item">
                <i className="flaticon-call" />
                <div className="contact-text">
                  <h2>Call Us</h2>
                  <p>+94 11 234 5678</p>
                </div>
              </div>
              <div className="contact-item">
                <i className="flaticon-send-mail" />
                <div className="contact-text">
                  <h2>Email Us</h2>
                  <p>support@activealuminium.com</p>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="contact-form">
              <form>
                <div className="form-group">
                  <input type="text" className="form-control" placeholder="Your Name" />
                </div>
                <div className="form-group">
                  <input type="email" className="form-control" placeholder="Your Email" />
                </div>
                <div className="form-group">
                  <textarea className="form-control" rows="4" placeholder="Message" />
                </div>
                <button type="submit" className="btn">
                  Send Message
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </>
);

export default ContactPage;

