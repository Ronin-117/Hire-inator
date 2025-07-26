// src/TailorPage.jsx

import { collection, getDocs, orderBy, query, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth, db } from './firebaseConfig';

const TailorPage = () => {
    const navigate = useNavigate();
    const [resumes, setResumes] = useState([]);
    const [selectedResumeId, setSelectedResumeId] = useState('');
    const [jobDescription, setJobDescription] = useState('');

    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

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
                    setSelectedResumeId(userResumes[0].id); // Pre-select the newest resume
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
        if (!selectedResumeId || !jobDescription) {
            setError("Please select a resume and provide a job description.");
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

            const response = await fetch('http://127.0.0.1:8000/api/tailor-resume/', {
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

    if (loading) return <h1>Loading your resumes...</h1>;

    return (
        <div>
            <Link to="/">← Back to Dashboard</Link>
            <h1>Tailor a Resume</h1>
            <p>Select a base resume, paste a job description, and the AI will create a new version tailored for the role.</p>

            <div style={{ marginBottom: '15px' }}>
                <label><strong>1. Select Base Resume:</strong></label><br/>
                <select value={selectedResumeId} onChange={(e) => setSelectedResumeId(e.target.value)} style={{width: '400px', padding: '5px'}}>
                    {resumes.map(resume => (
                        <option key={resume.id} value={resume.id}>{resume.resumeName}</option>
                    ))}
                </select>
            </div>

            <div style={{ marginBottom: '15px' }}>
                <label><strong>2. Paste Job Description:</strong></label><br/>
                <textarea 
                    rows="10" 
                    style={{width: '400px'}}
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the full job description here..."
                />
            </div>

            <button onClick={handleTailor} disabled={processing}>
                {processing ? 'Tailoring in Progress...' : 'Start Tailoring'}
            </button>

            {successMessage && <p style={{ color: 'green', marginTop: '15px' }}>{successMessage}</p>}
            {error && <p style={{ color: 'red', marginTop: '15px' }}>{error}</p>}
        </div>
    );
};

export default TailorPage;