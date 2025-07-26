import { onAuthStateChanged, signOut } from "firebase/auth";
import { useEffect, useState } from 'react';
import { Link, Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'; // Import router components
import EditorPage from './EditorPage';
import { auth } from './firebaseConfig';
import LoginPage from './LoginPage';
import ProfilePage from './ProfilePage'; // Import the new ProfilePage
import TailorPage from './TailorPage';
import UploadPage from './UploadPage';

// A new component for our main dashboard content
const Dashboard = () => (
    <div>
        <h3>Dashboard</h3>
        <nav>
            <Link to="/profile"><button>Go to Profile</button></Link>
            {/* Add links for other buttons later */}
            <Link to="/upload"><button>Upload Resume</button></Link>
            <Link to="/tailor"><button>Tailor Resume</button></Link>
        </nav>
    </div>
);

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setLoading(false);
        });
        return () => unsubscribe();
    }, []);

    const handleLogout = () => {
        signOut(auth).catch((error) => console.error("Logout Error:", error));
    };

    if (loading) {
        return <h1>Loading...</h1>;
    }

    return (
        <Router>
            <div className="App">
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h1>Hire-inator</h1>
                    {user && <button onClick={handleLogout}>Log Out</button>}
                </header>
                <hr />

                <Routes>
                    <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
                    <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" />} />
                    <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
                    <Route path="/upload" element={user ? <UploadPage /> : <Navigate to="/login" />} />
                    <Route path="/tailor" element={user ? <TailorPage /> : <Navigate to="/login" />} />
                    <Route path="/editor/:resumeId" element={user ? <EditorPage /> : <Navigate to="/login" />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;