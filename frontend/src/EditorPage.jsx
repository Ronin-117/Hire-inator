// src/EditorPage.jsx

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import './EditorPage.css';
import { auth } from './firebaseConfig';

import config from "./config";

const EditorPage = () => {

    const { resumeId } = useParams();
    const [resumeData, setResumeData] = useState(null);
    const [pdfUrl, setPdfUrl] = useState('');
    const [chatInput, setChatInput] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isRefining, setIsRefining] = useState(false);
    const [error, setError] = useState('');

    const refreshPdf = async () => {
        if (!auth.currentUser) return;
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`${config.API_BASE_URL}/api/resumes/${resumeId}/download/`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!response.ok) throw new Error('Failed to compile and fetch PDF.');
            const blob = await response.blob();

            if (pdfUrl) {
                window.URL.revokeObjectURL(pdfUrl);
            }
            const url = window.URL.createObjectURL(blob);
            setPdfUrl(url);
        } catch (err) {
            console.error(err);
            setError("Could not generate PDF preview. Check for LaTeX compilation errors.");
        }
    };

    useEffect(() => {
        const loadInitialData = async () => {
            if (!auth.currentUser) return;
            setIsLoading(true);
            try {
                const token = await auth.currentUser.getIdToken();
                const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/`, {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (!response.ok) throw new Error('Failed to fetch resume data.');
                const data = await response.json();
                setResumeData(data);
                await refreshPdf();
            } catch (err) {
                console.error(err);
                setError(err.message);
            }
            setIsLoading(false);
        };
        loadInitialData();
    }, [resumeId]);

    const handleRefine = async () => {
        if (!chatInput.trim() || !resumeData) return;
        setIsRefining(true);
        setError('');
        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            formData.append('instruction', chatInput);
            formData.append('job_description', resumeData.jobDescription || '');
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/refine/`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to refine resume.');
            setChatInput('');
            await refreshPdf();
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setIsRefining(false);
        }
    };

    if (isLoading) return <h1 className="editor-header">Generating Initial PDF Preview...</h1>;

    return (
        <div className="editor-container">
            <Link to="/profile">← Back to Tailor</Link>
            <h1 className="editor-header">Resume Editor: {resumeData?.resumeName}</h1>
            
            {error && <p className="error-message"><strong>Error:</strong> {error}</p>}
            
            <div className="editor-layout">
                {/* PDF Viewer Column */}
                <div className="pdf-viewer-panel">
                    {pdfUrl ? (
                        <iframe src={pdfUrl} width="100%" height="100%" title="Resume Preview"></iframe>
                    ) : (
                        <div className="pdf-viewer-placeholder">
                            <p>Loading Preview...</p>
                        </div>
                    )}
                </div>

                {/* Chat and Controls Column */}
                <div className="control-panel">
                    <h3>Refine-inator</h3>
                    <p>Give the AI further instructions to modify your resume.</p>
                    <textarea 
                        className="chat-textarea"
                        rows="12" 
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="e.g., 'Make the summary more concise' or 'Change the first bullet point under Tech Solutions to highlight data processing.'"
                    />
                    <button className="btn" onClick={handleRefine} disabled={isRefining}>
                        {isRefining ? 'Updating...' : 'Send Instruction'}
                    </button>
                    
                    <hr/>

                    <h3>Finalize-inator</h3>
                    <button className="btn btn-secondary">Save and Finalize</button>
                    <a href={pdfUrl} download={`${resumeData?.resumeName || 'resume'}.pdf`}>
                        <button className="btn btn-secondary" disabled={!pdfUrl}>Download Current PDF</button>
                    </a>
                </div>
            </div>
        </div>
    );
};

export default EditorPage;