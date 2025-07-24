// src/LoginPage.jsx

import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithPopup
} from "firebase/auth";
import { useState } from 'react';
import { auth, googleProvider } from './firebaseConfig';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    const handleEmailPasswordSignUp = async () => {
        setError(null); // Clear previous errors
        try {
            await createUserWithEmailAndPassword(auth, email, password);
            // The user is automatically signed in after successful creation
            console.log("User created and signed in successfully!");
        } catch (err) {
            console.error("Error signing up:", err);
            setError(err.message);
        }
    };

    const handleEmailPasswordLogin = async () => {
        setError(null);
        try {
            await signInWithEmailAndPassword(auth, email, password);
            console.log("User logged in successfully!");
        } catch (err) {
            console.error("Error logging in:", err);
            setError(err.message);
        }
    };

    const handleGoogleSignIn = async () => {
        setError(null);
        try {
            await signInWithPopup(auth, googleProvider);
            console.log("User signed in with Google successfully!");
        } catch (err) {
            console.error("Error with Google sign-in:", err);
            setError(err.message);
        }
    };

    return (
        <div>
            <h2>Login or Sign Up</h2>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
            />
            <br />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            <br />
            <button onClick={handleEmailPasswordLogin}>Log In</button>
            <button onClick={handleEmailPasswordSignUp}>Sign Up</button>
            <hr />
            <button onClick={handleGoogleSignIn}>Sign In with Google</button>

            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
};

export default LoginPage;