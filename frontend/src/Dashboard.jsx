// src/Dashboard.jsx
import { Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
    return (
        <div className="dashboard-container">
            <h2 className="dashboard-header">- Control Panel -</h2>
            <nav className="dashboard-nav">
                
                <Link to="/profile" className="nav-card">
                    <i className="fas fa-user-cog nav-card-icon"></i>
                    <h3>Profile</h3>
                    <p>Configure user settings and your global AI instructions.</p>
                </Link>
                
                <Link to="/upload" className="nav-card">
                    <i className="fas fa-file-arrow-up nav-card-icon"></i>
                    <h3>Upload</h3>
                    <p>Convert existing PDF resumes or import .tex files.</p>
                </Link>
                
                <Link to="/tailor" className="nav-card">
                    <i className="fas fa-crosshairs nav-card-icon"></i>
                    <h3>Tailor</h3>
                    <p>Adapt a resume for a specific job description.</p>
                </Link>

            </nav>
        </div>
    );
};

export default Dashboard;