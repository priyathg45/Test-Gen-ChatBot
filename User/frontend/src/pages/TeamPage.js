import React from 'react';

const TeamPage = () => (
  <>
    <div className="page-header">
      <h2>Our Team</h2>
    </div>
    <div className="team">
      <div className="container">
        <div className="section-header text-center">
          <p>Our Team</p>
          <h2>Active Aluminium Windows Operations &amp; Support</h2>
        </div>
        <div className="row">
          <div className="col-lg-3 col-md-6">
            <div className="team-item">
              <div className="team-text">
                <h2>Operations Lead</h2>
                <p>Production Oversight</p>
              </div>
            </div>
          </div>
          <div className="col-lg-3 col-md-6">
            <div className="team-item">
              <div className="team-text">
                <h2>Production Planner</h2>
                <p>Capacity &amp; Scheduling</p>
              </div>
            </div>
          </div>
          <div className="col-lg-3 col-md-6">
            <div className="team-item">
              <div className="team-text">
                <h2>Quality Specialist</h2>
                <p>Standards &amp; Checks</p>
              </div>
            </div>
          </div>
          <div className="col-lg-3 col-md-6">
            <div className="team-item">
              <div className="team-text">
                <h2>Support Engineer</h2>
                <p>System &amp; Users</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </>
);

export default TeamPage;

