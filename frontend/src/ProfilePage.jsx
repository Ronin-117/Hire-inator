// src/ProfilePage.jsx (Fetches real resumes)

import { collection, doc, getDoc, getDocs, orderBy, query, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auth, db } from './firebaseConfig';

const ProfilePage = () => {
    // --- State variables (no changes here) ---
    const [isEditing, setIsEditing] = useState(false);
    const [loadingProfile, setLoadingProfile] = useState(true);
    const [loadingResumes, setLoadingResumes] = useState(true); // <-- Separate loading for resumes
    const [error, setError] = useState(null);
    const [statusMessage, setStatusMessage] = useState('');
    const [profileData, setProfileData] = useState({ displayName: '', customInstructions: '' });
    const [formData, setFormData] = useState({ displayName: '', customInstructions: '' });
    
    // --- NEW: State for the REAL resume list ---
    const [resumes, setResumes] = useState([]); // Will hold data from Firestore

    // --- useEffect to fetch all data on component load ---
    useEffect(() => {
        if (!auth.currentUser) {
            setLoadingProfile(false);
            setLoadingResumes(false);
            return;
        }

        // --- 1. Fetch User Profile Data (no changes to this part) ---
        const fetchUserData = async () => {
            const userDocRef = doc(db, 'users', auth.currentUser.uid);
            try {
                const docSnap = await getDoc(userDocRef);
                if (docSnap.exists()) {
                    const userData = docSnap.data();
                    const fetchedData = {
                        displayName: userData.displayName || '',
                        customInstructions: userData.customInstructions || '',
                    };
                    setProfileData(fetchedData);
                    setFormData(fetchedData);
                } else {
                    setFormData({ displayName: auth.currentUser.displayName || '', customInstructions: '' });
                }
            } catch (err) {
                setError("Could not fetch profile data.");
                console.error("Fetch profile error:", err);
            }
            setLoadingProfile(false);
        };

        // --- 2. NEW: Fetch User's Resumes ---
        const fetchResumes = async () => {
            try {
                // Create a reference to the 'resumes' collection
                const resumesCollectionRef = collection(db, 'resumes');

                // Create a query against the collection
                const q = query(
                    resumesCollectionRef, 
                    where("userId", "==", auth.currentUser.uid), // Filter by the logged-in user's ID
                    orderBy("createdAt", "desc") // Show the newest resumes first
                );

                // Execute the query
                const querySnapshot = await getDocs(q);

                // Map the results to an array
                const userResumes = [];
                querySnapshot.forEach((doc) => {
                    userResumes.push({ 
                        id: doc.id, // The unique document ID
                        ...doc.data() // The rest of the data (resumeName, createdAt, etc.)
                    });
                });

                setResumes(userResumes);
                console.log("Fetched resumes:", userResumes);

            } catch (err) {
                setError("Could not fetch resumes.");
                console.error("Fetch resumes error:", err);
            }
            setLoadingResumes(false);
        };

        fetchUserData();
        fetchResumes();

    }, []); // Empty dependency array ensures this runs only once on mount

    // --- handleSaveProfile and other handlers remain unchanged ---
    const handleInputChange = (e) => { /* ... */ };
    const handleSaveProfile = async () => { /* ... */ };
    const handleCancel = () => { /* ... */ };


    return (
        <div>
            <Link to="/">← Back to Dashboard</Link>
            <h1>My Profile</h1>
            {/* ... error/status messages and profile edit form are unchanged ... */}
            
            <hr />

            <h3>My Resumes</h3>
            {loadingResumes ? (
                <p>Loading your resumes...</p>
            ) : resumes.length > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {resumes.map(resume => (
                        <li key={resume.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '5px' }}>
                            <strong>{resume.resumeName}</strong>
                            <br />
                            <small>
                                Created: {resume.createdAt ? resume.createdAt.toDate().toLocaleDateString() : 'N/A'}
                            </small>
                            <br />
                            {/* We will add functionality to these buttons later */}
                            <button>View/Edit</button>
                            <button>Download PDF</button>
                            <button style={{color: 'red'}}>Delete</button>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>You haven't uploaded any resumes yet. Go to the "Upload Resume" page to get started!</p>
            )}
        </div>
    );
};

export default ProfilePage;