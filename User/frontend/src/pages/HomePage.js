import React from 'react';

const HomePage = () => (
  <>
    {/* Carousel, feature, about, fact, service, team, FAQ, testimonial, blog */}
    {/* For brevity, start with a simple hero; you can progressively port full sections from HTML */}
    <div className="page-header" style={{ marginBottom: 0 }}>
      <h2>Streamlining Aluminium Joinery</h2>
    </div>
    <div className="about">
      <div className="container">
        <div className="row align-items-center">
          <div className="col-lg-7 col-md-12">
            <div className="section-header text-left">
              <p>About The System</p>
              <h2>Technology-Driven Aluminium Production</h2>
            </div>
            <div className="about-text">
              <p>
                Active Aluminium Windows (AAW) is a centralized production ecosystem designed to connect
                Administrators, Supervisors, and Workers across the full lifecycle from raw materials to
                installation.
              </p>
              <p>
                Use this React frontend to explore projects, teams, and services while your AI assistant helps
                answer questions in real time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </>
);

export default HomePage;

