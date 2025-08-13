// src/App.jsx

import { onAuthStateChanged, signOut } from "firebase/auth";
import { useEffect, useState } from 'react';
import { Link, Navigate, Route, BrowserRouter as Router, Routes, useLocation } from 'react-router-dom';
import { auth } from './firebaseConfig';

import Dashboard from './Dashboard';
import EditorPage from './EditorPage';
import LoginPage from './LoginPage';
import ProfilePage from './ProfilePage';
import TailorPage from './TailorPage';
import UploadPage from './UploadPage';

import './App.css';


const AppLayout = ({ user }) => {
    const location = useLocation();
    const showHeader = location.pathname !== '/login';

    const handleLogout = () => {
        signOut(auth).catch((error) => console.error("Logout Error:", error));
    };

    return (
        <div className="App">
            {showHeader && (
                <header style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.5rem 2rem', borderBottom: '2px solid var(--black)',
                    backgroundColor: 'var(--white)', color: 'var(--black)'
                }}>
                    <Link to="/" style={{ textDecoration: 'none', color: 'var(--purple)' }}>
                        <h1 style={{ fontSize: '1.5rem', textTransform: 'uppercase', margin: 0 }}>Hire-inator</h1>
                    </Link>
                    {user && (
                        <button onClick={handleLogout} style={{
                            padding: '8px 15px', border: '2px solid var(--purple)',
                            backgroundColor: 'transparent', color: 'var(--purple)',
                            fontWeight: 'bold', borderRadius: '5px'
                        }}>
                            Log Out
                        </button>
                    )}
                </header>
            )}
            
            <main>
                <Routes>
                    <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
                    <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
                    <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" />} />
                    <Route path="/upload" element={user ? <UploadPage /> : <Navigate to="/login" />} />
                    <Route path="/tailor" element={user ? <TailorPage /> : <Navigate to="/login" />} />
                    <Route path="/editor/:resumeId" element={user ? <EditorPage /> : <Navigate to="/login" />} />
                </Routes>
            </main>
        </div>
    );
};

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

    if (loading) {
        return <h1 style={{ textAlign: 'center', marginTop: '2rem' }}>Loading Application...</h1>;
    }

    return (
        <Router>
            <AppLayout user={user} />
        </Router>
    );
}

export default App;