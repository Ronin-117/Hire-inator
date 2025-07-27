// src/LoginPage.jsx (Corrected)

import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithPopup
} from "firebase/auth";
import { useState } from 'react';
import { auth, googleProvider } from './firebaseConfig';
import './LoginPage.css'; // Import the styles

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    // --- Firebase logic handlers ---
    const handleEmailPasswordSignUp = async (e) => {
        e.preventDefault(); // Prevent form submission
        setError(null);
        try {
            await createUserWithEmailAndPassword(auth, email, password);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleEmailPasswordLogin = async (e) => {
        e.preventDefault(); // Prevent form submission
        setError(null);
        try {
            await signInWithEmailAndPassword(auth, email, password);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleGoogleSignIn = async () => {
        setError(null);
        try {
            await signInWithPopup(auth, googleProvider);
        } catch (err) {
            setError(err.message);
        }
    };

    const GoogleIcon = () => (
        <svg className="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="white">
            <path d="M22.56,12.25C22.56,11.47 22.49,10.72 22.36,10H12V14.25H18.06C17.74,15.75 16.81,17.03 15.36,18V20.75H19.09C21.2,18.83 22.56,15.83 22.56,12.25Z" fill="#4285F4"/>
            <path d="M12,23C15.09,23 17.72,21.92 19.5,20.14L15.86,17.5C14.7,18.33 13.45,18.75 12,18.75C9.13,18.75 6.69,16.89 5.86,14.25H2.12V17C3.93,20.59 7.69,23 12,23Z" fill="#34A853"/>
            <path d="M5.86,14.25C5.66,13.75 5.56,13.22 5.56,12.67C5.56,12.12 5.66,11.59 5.86,11.09V8.34H2.12C1.42,9.64 1,11.12 1,12.67C1,14.22 1.42,15.7 2.12,17L5.86,14.25Z" fill="#FBBC05"/>
            <path d="M12,5.25C13.56,5.25 14.94,5.83 15.96,6.8L18.66,4.12C16.89,2.34 14.61,1.33 12,1.33C7.69,1.33 3.93,3.75 2.12,7.34L5.86,10C6.69,7.41 9.13,5.25 12,5.25Z" fill="#EA4335"/>
        </svg>
    );

    return (
        <div className="login-page">
            <div className="login-container">
                <h2>Hire-inator</h2>
                
                {/* We use a <form> element for better accessibility */}
                <form onSubmit={handleEmailPasswordLogin}>
                    <div className="input-group">
                        <input
                            className="input-field"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Email Address"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input
                            className="input-field"
                            type="password"
                            value={password}
                            // --- THIS IS THE CRITICAL FIX ---
                            onChange={(e) => setPassword(e.target.value)}
                            // --- WAS: e.targe.value ---
                            placeholder="Password"
                            required
                        />
                    </div>

                    <div className="button-group">
                        <button type="submit" className="btn btn-primary">Log In</button>
                        <button type="button" className="btn btn-secondary" onClick={handleEmailPasswordSignUp}>Sign Up</button>
                    </div>
                </form>

                <hr className="divider" />

                <button type="button" className="btn btn-google" onClick={handleGoogleSignIn}>
                    <GoogleIcon />
                    Sign In with Google
                </button>

                {error && <p className="error-message">{error}</p>}
            </div>
        </div>
    );
};

export default LoginPage;