// src/ProfilePage.jsx (No Profile Picture Version)

import { doc, getDoc, setDoc } from 'firebase/firestore'; // Firestore functions
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auth, db } from './firebaseConfig'; // We only need auth and db

// Resume list logic remains the same (for now)
const fakeResumes = [
    { id: 'resume1', name: 'Software Engineer Resume', lastUpdated: '2025-07-20' },
    { id: 'resume2', name: 'Data Analyst Resume (Tailored for Google)', lastUpdated: '2025-07-22' },
];

const ProfilePage = () => {
    // --- UI State ---
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [statusMessage, setStatusMessage] = useState('');

    // --- Data State (Simplified) ---
    // This state holds the data as it is stored in Firestore
    const [profileData, setProfileData] = useState({
        displayName: '',
        customInstructions: '',
    });
    // This state holds the data currently being edited in the form
    const [formData, setFormData] = useState({
        displayName: '',
        customInstructions: '',
    });
    
    // --- useEffect to fetch data ---
    useEffect(() => {
        setLoading(true);
        const fetchUserData = async () => {
            if (auth.currentUser) {
                const userDocRef = doc(db, 'users', auth.currentUser.uid);
                try {
                    const docSnap = await getDoc(userDocRef);
                    if (docSnap.exists()) {
                        const userData = docSnap.data();
                        const fetchedData = {
                            displayName: userData.displayName || '',
                            customInstructions: userData.customInstructions || '',
                        };
                        setProfileData(fetchedData); // Store the original data
                        setFormData(fetchedData);   // Set the form fields
                    } else {
                        // If no profile in Firestore, use default from Auth object
                        const defaultData = {
                            displayName: auth.currentUser.displayName || '',
                            customInstructions: '',
                        };
                        setProfileData(defaultData);
                        setFormData(defaultData);
                    }
                } catch (err) {
                    setError("Could not fetch profile data.");
                    console.error("Fetch profile error:", err);
                }
            }
        };

        fetchUserData();
        // We can set loading to false here as we aren't waiting for resumes anymore
        setLoading(false);
    }, []); // Runs once when the component mounts

    // Handles changes to any text input
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleSaveProfile = async () => {
        if (!auth.currentUser) return setError("You must be logged in.");

        setStatusMessage("Saving profile...");
        const userDocRef = doc(db, 'users', auth.currentUser.uid);
        try {
            // The data to save is simply the current state of the form
            await setDoc(userDocRef, formData, { merge: true });
            
            setProfileData(formData); // Update the "original" data state with the new saved data
            setIsEditing(false);      // Exit edit mode
            setStatusMessage("Profile saved successfully!");
            setTimeout(() => setStatusMessage(''), 3000); // Clear message after 3 seconds

        } catch (err) {
            setError("Failed to save profile.");
            console.error("Save profile error:", err);
            setStatusMessage('');
        }
    };
    
    const handleCancel = () => {
        setFormData(profileData); // Revert form changes back to the last saved state
        setIsEditing(false);
    };

    if (loading) return <h1>Loading Profile...</h1>;

    return (
        <div>
            <Link to="/">← Back to Dashboard</Link>
            <h1>My Profile</h1>

            {error && <p style={{ color: 'red' }}>{error}</p>}
            {statusMessage && <p style={{ color: 'blue' }}>{statusMessage}</p>}

            <div style={{ margin: '20px 0' }}>
                <h3>User Details</h3>
                <label>
                    Display Name:
                    <input
                        type="text"
                        name="displayName"
                        value={formData.displayName}
                        onChange={handleInputChange}
                        disabled={!isEditing}
                        placeholder="Your Name"
                    />
                </label>
            </div>
            
             <div>
                <h3>AI Custom Instructions</h3>
                <p>Instructions for tailoring your resume (e.g., "Always use a professional tone").</p>
                <textarea
                    name="customInstructions"
                    rows="4"
                    cols="50"
                    value={formData.customInstructions}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Enter instructions for the AI..."
                />
            </div>

            {isEditing ? (
                <div>
                    <button onClick={handleSaveProfile}>Save Changes</button>
                    <button onClick={handleCancel}>Cancel</button>
                </div>
            ) : (
                <button onClick={() => setIsEditing(true)}>Edit Profile</button>
            )}
            
            <hr />

            <h3>My Resumes (Placeholder)</h3>
            <ul>
                {fakeResumes.map(resume => (
                    <li key={resume.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '5px' }}>
                        <strong>{resume.name}</strong>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ProfilePage;