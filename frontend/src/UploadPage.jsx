// src/UploadPage.jsx (Complete Code)

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { auth } from './firebaseConfig';

const UploadPage = () => {
    // State for the PDF upload form
    const [pdfFile, setPdfFile] = useState(null);
    const [pdfResumeName, setPdfResumeName] = useState('');

    // State for the TeX upload form
    const [texFile, setTexFile] = useState(null);
    const [texResumeName, setTexResumeName] = useState('');

    // Shared state for UI feedback messages
    const [statusMessage, setStatusMessage] = useState('');
    const [error, setError] = useState('');

    // --- Handlers for PDF Upload ---
    const handlePdfFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setPdfFile(selectedFile);
            // Pre-fill the name input with the filename for user convenience
            const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
            setPdfResumeName(fileNameWithoutExt);
        }
    };
    
    const handlePdfUpload = async () => {
        if (!pdfFile) {
            setError('Please select a PDF file first.');
            return;
        }
        if (!auth.currentUser) {
            setError('You must be logged in to upload a resume.');
            return;
        }

        setError('');
        setStatusMessage('Starting PDF upload...');

        try {
            const token = await auth.currentUser.getIdToken();

            const formData = new FormData();
            formData.append('resume_pdf', pdfFile); // Key for the file
            formData.append('resume_name', pdfResumeName); // Key for the name

            setStatusMessage('PDF selected. Sending to AI for conversion... (This may take several seconds)');
            
            const response = await fetch('http://127.0.0.1:8000/api/upload-resume/', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token,
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong on the server.');
            }
            
            setStatusMessage(`Success! PDF resume saved as '${pdfResumeName}'. ID: ${data.resumeId}`);
            setPdfFile(null);
            setPdfResumeName('');
            
        } catch (err) {
            console.error('PDF upload failed:', err);
            setError(err.message);
            setStatusMessage('');
        }
    };


    // --- Handlers for TeX Upload ---
    const handleTexFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setTexFile(selectedFile);
            const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
            setTexResumeName(fileNameWithoutExt);
        }
    };

    const handleTexUpload = async () => {
        if (!texFile) {
            setError('Please select a .tex file first.');
            return;
        }
        if (!auth.currentUser) {
            setError('You must be logged in.');
            return;
        }

        setError('');
        setStatusMessage('Uploading .tex file...');

        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            formData.append('resume_tex', texFile); // This key must match the new Django view
            formData.append('resume_name', texResumeName);

            const response = await fetch('http://127.0.0.1:8000/api/upload-tex/', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong.');
            }
            
            setStatusMessage(`Success! TeX resume saved as '${texResumeName}'. ID: ${data.resumeId}`);
            setTexFile(null);
            setTexResumeName('');
            
        } catch (err) {
            console.error('TeX upload failed:', err);
            setError(err.message);
            setStatusMessage('');
        }
    };


    return (
        <div>
            <Link to="/">← Back to Dashboard</Link>
            <h1>Upload or Import a Resume</h1>

            {/* --- PDF UPLOAD SECTION --- */}
            <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                <h2>Option 1: Upload a PDF to Convert with AI</h2>
                <p>Select a PDF file to convert into a new LaTeX resume.</p>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        PDF File:
                        <input type="file" accept=".pdf" onChange={handlePdfFileChange} />
                    </label>
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        Save As:
                        <input 
                            type="text" 
                            value={pdfResumeName} 
                            onChange={(e) => setPdfResumeName(e.target.value)} 
                            placeholder="e.g., Software Engineer Resume" 
                            style={{ width: '300px' }} 
                        />
                    </label>
                </div>
                <button onClick={handlePdfUpload} disabled={!pdfFile}>Upload and Convert PDF</button>
            </div>


            {/* --- TEX UPLOAD SECTION --- */}
            <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
                <h2>Option 2: Import an Existing .tex File</h2>
                <p>If you already have a resume in LaTeX format, you can upload it directly.</p>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        .tex File:
                        <input type="file" accept=".tex, .txt" onChange={handleTexFileChange} />
                    </label>
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        Save As:
                        <input 
                            type="text" 
                            value={texResumeName} 
                            onChange={(e) => setTexResumeName(e.target.value)} 
                            placeholder="e.g., Imported TeX Resume" 
                            style={{ width: '300px' }} 
                        />
                    </label>
                </div>
                <button onClick={handleTexUpload} disabled={!texFile}>Upload .tex File</button>
            </div>


            {/* Shared status messages at the bottom */}
            {statusMessage && <p style={{ color: 'blue', marginTop: '20px', fontWeight: 'bold' }}>{statusMessage}</p>}
            {error && <p style={{ color: 'red', marginTop: '20px', fontWeight: 'bold' }}>{error}</p>}
        </div>
    );
};

export default UploadPage;