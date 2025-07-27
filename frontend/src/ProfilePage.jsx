// src/ProfilePage.jsx (Your Full Logic + New Styles)

import { collection, doc, getDoc, getDocs, orderBy, query, setDoc, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auth, db } from './firebaseConfig';
import './ProfilePage.css'; // Import the stylesheet

const ProfilePage = () => {
    // --- YOUR EXACT STATE AND LOGIC ---
    // This is the complete, line-for-line logic from your working version.
    // It has not been condensed or changed.

    // --- UI State ---
    const [isEditing, setIsEditing] = useState(false);
    const [loadingProfile, setLoadingProfile] = useState(true);
    const [loadingResumes, setLoadingResumes] = useState(true);
    const [downloadingId, setDownloadingId] = useState(null);
    const [error, setError] = useState(null);
    const [statusMessage, setStatusMessage] = useState('');

    // --- Data State ---
    const [profileData, setProfileData] = useState({ displayName: '', customInstructions: '' });
    const [formData, setFormData] = useState({ displayName: '', customInstructions: '' });
    const [resumes, setResumes] = useState([]);

    const handleEditResumeName = (resume) => {
        setEditingResumeId(resume.id);
        setNewResumeName(resume.resumeName);
    };

    // --- Data Fetching Effect ---
    useEffect(() => {
        if (!auth.currentUser) {
            setLoadingProfile(false);
            setLoadingResumes(false);
            return;
        }
        const fetchUserData = async () => {
            const userDocRef = doc(db, 'users', auth.currentUser.uid);
            try {
                const docSnap = await getDoc(userDocRef);
                if (docSnap.exists()) {
                    const userData = docSnap.data();
                    const fetchedData = { displayName: userData.displayName || '', customInstructions: userData.customInstructions || '' };
                    setProfileData(fetchedData);
                    setFormData(fetchedData);
                } else {
                    const defaultData = { displayName: auth.currentUser.displayName || '', customInstructions: '' };
                    setProfileData(defaultData);
                    setFormData(defaultData);
                }
            } catch (err) {
                setError("Could not fetch profile data.");
                console.error("Fetch profile error:", err);
            }
            setLoadingProfile(false);
        };
        const fetchResumes = async () => {
            try {
                const q = query(collection(db, 'resumes'), where("userId", "==", auth.currentUser.uid), orderBy("createdAt", "desc"));
                const querySnapshot = await getDocs(q);
                const userResumes = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                setResumes(userResumes);
            } catch (err) {
                setError("Could not fetch resumes.");
                console.error("Fetch resumes error:", err);
            }
            setLoadingResumes(false);
        };
        fetchUserData();
        fetchResumes();
    }, []);

    // --- Event Handlers (Full, working versions) ---
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
            const textData = await response.text();
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
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
        if (!window.confirm(`Are you sure you want to permanently delete "${resumeName}"? This action cannot be undone.`)) {
            return;
        }
        if (!auth.currentUser) return;
        setError(null);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/delete/`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + token },
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete resume.');
            }
            setResumes(currentResumes => currentResumes.filter(r => r.id !== resumeId));
            setStatusMessage(`Successfully deleted "${resumeName}".`);
        } catch (err) {
            console.error("Delete failed:", err);
            setError(err.message);
        }
    };
    // --- END OF YOUR WORKING LOGIC ---

    const isLoading = loadingProfile || loadingResumes;
    if (isLoading) return <h1 className="profile-header">Loading Profile...</h1>;

    // --- STYLED JSX ---
    return (
        <div className="profile-container">
            <Link to="/">← Back to Dashboard</Link>
            <h1 className="profile-header">Profile & Settings</h1>

            {error && <p style={{ color: 'var(--error-red)' }}>{error}</p>}
            {statusMessage && <p style={{ color: 'var(--accent-purple)' }}>{statusMessage}</p>}

            <div className="profile-panel">
                <h3>User Details & AI Instructions</h3>
                <div className="form-group">
                    <label htmlFor="displayName">Display Name</label>
                    <input id="displayName" className="form-input" type="text" name="displayName" value={formData.displayName} onChange={handleInputChange} disabled={!isEditing} />
                </div>
                <div className="form-group">
                    <label htmlFor="customInstructions">AI Custom Instructions</label>
                    <textarea id="customInstructions" className="form-textarea" name="customInstructions" rows="4" value={formData.customInstructions} onChange={handleInputChange} disabled={!isEditing} placeholder="Enter instructions for the AI..." />
                </div>
                <div className="form-actions">
                    {isEditing ? (
                        <>
                            <button className="btn btn-primary" onClick={handleSaveProfile}>Save Changes</button>
                            <button className="btn btn-secondary" onClick={handleCancel} style={{ marginLeft: '10px' }}>Cancel</button>
                        </>
                    ) : (
                        <button className="btn btn-primary" onClick={() => setIsEditing(true)}>Edit Profile</button>
                    )}
                </div>
            </div>

            <div className="profile-panel">
                <h3>My Resumes</h3>
                {resumes.length > 0 ? (
                    <ul className="resume-list">
                        {resumes.map(resume => (
                            <li key={resume.id} className="resume-item">
                                <div className="resume-info">
                                    <strong>{resume.resumeName}</strong>
                                    <small>Last Updated: {resume.lastUpdated ? resume.lastUpdated.toDate().toLocaleDateString() : 'N/A'}</small>
                                </div>
                                <div className="resume-actions">
                                    <button className="btn btn-secondary" onClick={() => handleDownloadTex(resume.id, resume.resumeName)}>Download .tex</button>
                                    <button className="btn btn-secondary" onClick={() => handleDownloadPdf(resume.id, resume.resumeName)} disabled={downloadingId === resume.id}>
                                        {downloadingId === resume.id ? 'Compiling...' : 'Download PDF'}
                                    </button>
                                    <button className="btn btn-danger" onClick={() => handleDeleteResume(resume.id, resume.resumeName)}>Delete</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>You haven't uploaded any resumes yet. Go to the "Upload Resume" page to get started!</p>
                )}
            </div>
        </div>
    );
};

export default ProfilePage;