// src/ProfilePage.jsx (Complete Code)

import { collection, doc, getDoc, getDocs, orderBy, query, setDoc, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auth, db } from './firebaseConfig';

const ProfilePage = () => {
    // --- UI State ---
    const [isEditing, setIsEditing] = useState(false);
    const [loadingProfile, setLoadingProfile] = useState(true);
    const [loadingResumes, setLoadingResumes] = useState(true);
    const [downloadingId, setDownloadingId] = useState(null); // To show loading state on a specific download button
    const [error, setError] = useState(null);
    const [statusMessage, setStatusMessage] = useState('');

    // --- Data State ---
    const [profileData, setProfileData] = useState({ displayName: '', customInstructions: '' });
    const [formData, setFormData] = useState({ displayName: '', customInstructions: '' });
    const [resumes, setResumes] = useState([]);

    // --- Data Fetching Effect ---
    useEffect(() => {
        if (!auth.currentUser) {
            setLoadingProfile(false);
            setLoadingResumes(false);
            return;
        }

        // 1. Fetch User Profile Data
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
            setLoadingProfile(false);
        };

        // 2. Fetch User's Resumes
        const fetchResumes = async () => {
            try {
                const resumesCollectionRef = collection(db, 'resumes');
                const q = query(
                    resumesCollectionRef,
                    where("userId", "==", auth.currentUser.uid),
                    orderBy("createdAt", "desc")
                );
                const querySnapshot = await getDocs(q);
                const userResumes = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                setResumes(userResumes);
            } catch (err) {
                setError("Could not fetch resumes. You may need to create a Firestore index. Check the browser console (F12) for a link.");
                console.error("Fetch resumes error:", err);
            }
            setLoadingResumes(false);
        };

        fetchUserData();
        fetchResumes();
    }, []);

    // --- Event Handlers ---
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSaveProfile = async () => {
        if (!auth.currentUser) return;
        setStatusMessage("Saving...");
        const userDocRef = doc(db, 'users', auth.currentUser.uid);
        try {
            await setDoc(userDocRef, formData, { merge: true });
            setProfileData(formData);
            setIsEditing(false);
            setStatusMessage("Profile saved successfully!");
            setTimeout(() => setStatusMessage(''), 3000);
        } catch (err) {
            setError("Failed to save profile.");
            console.error("Save profile error:", err);
            setStatusMessage('');
        }
    };

    const handleCancel = () => {
        setFormData(profileData);
        setIsEditing(false);
    };

    const handleDownloadPdf = async (resumeId, resumeName) => {
        if (!auth.currentUser) return;
        setDownloadingId(resumeId);
        setError(null);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/download/`, {
                method: 'GET',
                headers: { 'Authorization': 'Bearer ' + token },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to download PDF.');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${resumeName || 'resume'}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Download failed:", err);
            setError(err.message);
        } finally {
            setDownloadingId(null);
        }
    };

    const handleDownloadTex = async (resumeId, resumeName) => {
        if (!auth.currentUser) return;
        setError(null);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/download-tex/`, {
                headers: { 'Authorization': 'Bearer ' + token },
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to download .tex file.');
            }

            // Get the text content from the response
            const textData = await response.text();
            // Create a blob of plain text
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            
            // Standard download trigger logic
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${resumeName || 'resume'}.tex`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("TeX Download failed:", err);
            setError(err.message);
        }
    };

    const handleDeleteResume = async (resumeId, resumeName) => {
        // CRITICAL: Confirm with the user before deleting!
        if (!window.confirm(`Are you sure you want to permanently delete "${resumeName}"? This action cannot be undone.`)) {
            return;
        }

        if (!auth.currentUser) return;
        setError(null);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/delete/`, {
                method: 'DELETE', // Use the correct HTTP method
                headers: { 'Authorization': 'Bearer ' + token },
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete resume.');
            }
            
            // Success! Update the UI instantly by removing the item from state.
            setResumes(currentResumes => currentResumes.filter(r => r.id !== resumeId));
            setStatusMessage(`Successfully deleted "${resumeName}".`);

        } catch (err) {
            console.error("Delete failed:", err);
            setError(err.message);
        }
    };

    const isLoading = loadingProfile || loadingResumes;
    if (isLoading) return <h1>Loading Profile...</h1>;

    return (
        <div>
            <Link to="/">← Back to Dashboard</Link>
            <h1>My Profile</h1>

            {error && <p style={{ color: 'red' }}>{error}</p>}
            {statusMessage && <p style={{ color: 'blue' }}>{statusMessage}</p>}

            <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                <h3>User Details</h3>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        Display Name:
                        <input
                            type="text" name="displayName" value={formData.displayName}
                            onChange={handleInputChange} disabled={!isEditing}
                        />
                    </label>
                </div>
                <div>
                    <h3>AI Custom Instructions</h3>
                    <textarea
                        name="customInstructions" rows="4" cols="50"
                        value={formData.customInstructions} onChange={handleInputChange}
                        disabled={!isEditing} placeholder="Enter instructions for the AI..."
                    />
                </div>
                <div style={{ marginTop: '10px' }}>
                    {isEditing ? (
                        <>
                            <button onClick={handleSaveProfile}>Save Changes</button>
                            <button onClick={handleCancel} style={{ marginLeft: '10px' }}>Cancel</button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)}>Edit Profile</button>
                    )}
                </div>
            </div>

            <hr />

            <h3>My Resumes</h3>
            {loadingResumes ? (
                <p>Loading your resumes...</p>
            ) : resumes.length > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {resumes.map(resume => (
                        <li key={resume.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong>{resume.resumeName}</strong>
                                <br />
                                <small>
                                    Last Updated: {resume.lastUpdated ? resume.lastUpdated.toDate().toLocaleDateString() : 'N/A'}
                                </small>
                            </div>
                            <div>
                                <button
                                    style={{ marginRight: '5px' }}
                                    onClick={() => handleDownloadTex(resume.id, resume.resumeName)}
                                >
                                    Download .tex
                                </button>
                                <button
                                    style={{ marginRight: '5px' }}
                                    onClick={() => handleDownloadPdf(resume.id, resume.resumeName)}
                                    disabled={downloadingId === resume.id}
                                >
                                    {downloadingId === resume.id ? 'Compiling...' : 'Download PDF'}
                                </button>
                                <button 
                                    style={{ color: 'white', backgroundColor: '#d9534f', border: 'none', padding: '5px 10px', cursor: 'pointer' }}
                                    onClick={() => handleDeleteResume(resume.id, resume.resumeName)}
                                >
                                    Delete
                                </button>
                            </div>
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