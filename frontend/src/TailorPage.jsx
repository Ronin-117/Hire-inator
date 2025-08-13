// src/TailorPage.jsx

import { collection, getDocs, orderBy, query, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth, db } from './firebaseConfig';
import './TailorPage.css';

import config from "./config";

const TailorPage = () => {
    const navigate = useNavigate();
    const [resumes, setResumes] = useState([]);
    const [selectedResumeId, setSelectedResumeId] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [newResumeName, setNewResumeName] = useState('');

    useEffect(() => {
        if (!auth.currentUser) return;
        const fetchResumes = async () => {
            try {
                const q = query(
                    collection(db, 'resumes'),
                    where("userId", "==", auth.currentUser.uid),
                    orderBy("createdAt", "desc")
                );
                const querySnapshot = await getDocs(q);
                const userResumes = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                setResumes(userResumes);
                if (userResumes.length > 0) {
                    setSelectedResumeId(userResumes[0].id);
                }
            } catch (err) {
                setError("Could not fetch your resumes.");
                console.error(err);
            }
            setLoading(false);
        };
        fetchResumes();
    }, []);

    const handleTailor = async () => {
        if (!selectedResumeId || !jobDescription || !newResumeName.trim()) {
            setError("Please select a resume, provide a job description, and give the new version a name.");
            return;
        }
        if (!auth.currentUser) return;
        setError('');
        setSuccessMessage('');
        setProcessing(true);
        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            formData.append('base_resume_id', selectedResumeId);
            formData.append('job_description', jobDescription);
            formData.append('new_resume_name', newResumeName);
            const response = await fetch(`${config.API_BASE_URL}/api/tailor-resume/`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Server error during tailoring.');
            }
            setSuccessMessage(`Success! Redirecting to editor...`);
            navigate(`/editor/${data.newResumeId}`);
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <h1 className="tailor-header">Loading your resumes...</h1>;

    return (
        <div className="tailor-container">
            <Link to="/">← Back to Dashboard</Link>
            <h1 className="tailor-header">Tailor-inator</h1>
            <p className="tailor-subheader">Select a base resume, paste a job description, and the AI will create a new version tailored for the role.</p>

            <div className="tailor-panel">
                <div className="tailor-form-group">
                    <label htmlFor="resume-select">1. Select Base Resume</label>
                    <select 
                        id="resume-select"
                        className="form-select"
                        value={selectedResumeId} 
                        onChange={(e) => setSelectedResumeId(e.target.value)}
                    >
                        {resumes.length > 0 ? (
                            resumes.map(resume => (
                                <option key={resume.id} value={resume.id}>{resume.resumeName}</option>
                            ))
                        ) : (
                            <option disabled>No resumes found. Please upload one first.</option>
                        )}
                    </select>
                </div>

                <div className="tailor-form-group">
                    <label htmlFor="jd-textarea">2. Paste Job Description</label>
                    <textarea 
                        id="jd-textarea"
                        className="form-textarea"
                        rows="12" 
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the full job description here..."
                    />
                </div>
                <div className="tailor-form-group">
                    <label htmlFor="new-name-input">3. Name Your New Tailored Resume</label>
                    <input
                        id="new-name-input"
                        type="text"
                        className="form-select" 
                        value={newResumeName}
                        onChange={(e) => setNewResumeName(e.target.value)}
                        placeholder="e.g., Resume for Google Backend Role"
                    />
                </div>

                <button className="btn-submit" onClick={handleTailor} disabled={processing || resumes.length === 0}>
                    {processing ? 'Tailoring in Progress...' : 'Start Tailoring'}
                </button>
            </div>

            {successMessage && <p className="status-message">{successMessage}</p>}
            {error && <p className="error-message">{error}</p>}
        </div>
    );
};

export default TailorPage;