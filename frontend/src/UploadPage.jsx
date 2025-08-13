// src/UploadPage.jsx

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { auth } from './firebaseConfig';
import './UploadPage.css';

import config from "./config";

const UploadPage = () => {
    // --- State for the PDF upload form ---
    const [pdfFile, setPdfFile] = useState(null);
    const [pdfResumeName, setPdfResumeName] = useState('');

    // --- State for the TeX upload form ---
    const [texFile, setTexFile] = useState(null);
    const [texResumeName, setTexResumeName] = useState('');

    const [formStatus, setFormStatus] = useState({
        pdf: { status: 'idle', message: '' },
        tex: { status: 'idle', message: '' },
    });

    // --- Handlers for PDF Upload ---
    const handlePdfFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setPdfFile(selectedFile);
            const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
            setPdfResumeName(fileNameWithoutExt);
            // Reset status if a new file is chosen
            setFormStatus(prev => ({ ...prev, pdf: { status: 'idle', message: '' } }));
        }
    };
    
    const handlePdfUpload = async () => {
        if (!pdfFile || !auth.currentUser) return;

        setFormStatus(prev => ({ ...prev, pdf: { status: 'loading', message: '' } }));

        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            formData.append('resume_pdf', pdfFile);
            formData.append('resume_name', pdfResumeName);
            
            const response = await fetch( `${config.API_BASE_URL}/api/upload-resume/`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Server error.');

            setFormStatus(prev => ({ ...prev, pdf: { status: 'success', message: `Saved as ${pdfResumeName}` } }));
            setPdfFile(null);
            setPdfResumeName('');
            
        } catch (err) {
            console.error('PDF upload failed:', err);
            setFormStatus(prev => ({ ...prev, pdf: { status: 'error', message: err.message } }));
        } finally {
            // Revert button to idle state after 3 seconds
            setTimeout(() => {
                setFormStatus(prev => ({ ...prev, pdf: { status: 'idle', message: '' } }));
            }, 3000);
        }
    };

    // --- Handlers for TeX Upload ---
    const handleTexFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setTexFile(selectedFile);
            const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
            setTexResumeName(fileNameWithoutExt);
            setFormStatus(prev => ({ ...prev, tex: { status: 'idle', message: '' } }));
        }
    };

    const handleTexUpload = async () => {
        if (!texFile || !auth.currentUser) return;
        
        setFormStatus(prev => ({ ...prev, tex: { status: 'loading', message: '' } }));

        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            formData.append('resume_tex', texFile);
            formData.append('resume_name', texResumeName);

            const response = await fetch(`${config.API_BASE_URL}/api/upload-tex/`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Server error.');
            
            setFormStatus(prev => ({ ...prev, tex: { status: 'success', message: `Saved as ${texResumeName}` } }));
            setTexFile(null);
            setTexResumeName('');
            
        } catch (err) {
            console.error('TeX upload failed:', err);
            setFormStatus(prev => ({ ...prev, tex: { status: 'error', message: err.message } }));
        } finally {
            // Revert button to idle state after 3 seconds
            setTimeout(() => {
                setFormStatus(prev => ({ ...prev, tex: { status: 'idle', message: '' } }));
            }, 3000);
        }
    };

    // --- Helper function to determine button text and color ---
    const getButtonContent = (formType) => {
        const { status } = formStatus[formType];
        let text = formType === 'pdf' ? 'Upload & Convert PDF' : 'Upload .tex File';
        let className = 'btn';

        switch (status) {
            case 'loading':
                text = 'Processing...';
                break;
            case 'success':
                text = 'Success!';
                className += ' btn-success';
                break;
            case 'error':
                text = 'Error!';
                className += ' btn-danger'; 
                break;
            default:
                break;
        }
        return { text, className };
    };

    return (
        <div className="upload-container">
            <Link to="/">← Back to Dashboard</Link>
            <h1 className="upload-header">Upload or Import a Resume</h1>

            {/* --- PDF UPLOAD SECTION --- */}
            <div className="upload-panel">
                <h2>Option 1: Upload a PDF to Convert with AI</h2>
                <p>Select a PDF file to convert into a new LaTeX resume.</p>
                <div className="upload-form-group">
                    <label htmlFor="pdf-file-input">PDF File:</label>
                    <input id="pdf-file-input" type="file" accept=".pdf" onChange={handlePdfFileChange} />
                </div>
                <div className="upload-form-group">
                    <label htmlFor="pdf-name-input">Save As:</label>
                    <input 
                        id="pdf-name-input"
                        type="text" 
                        value={pdfResumeName} 
                        onChange={(e) => setPdfResumeName(e.target.value)} 
                        placeholder="e.g., Software Engineer Resume" 
                    />
                </div>
                <button 
                    className={getButtonContent('pdf').className}
                    onClick={handlePdfUpload} 
                    disabled={!pdfFile || formStatus.pdf.status === 'loading'}
                >
                    {getButtonContent('pdf').text}
                </button>
                {formStatus.pdf.status === 'error' && <p className="error-message">{formStatus.pdf.message}</p>}
            </div>

            {/* --- TEX UPLOAD SECTION --- */}
            <div className="upload-panel">
                <h2>Option 2: Import an Existing .tex File</h2>
                <p>If you already have a resume in LaTeX format, you can upload it directly.</p>
                <div className="upload-form-group">
                    <label htmlFor="tex-file-input">.tex File:</label>
                    <input id="tex-file-input" type="file" accept=".tex,.txt" onChange={handleTexFileChange} />
                </div>
                <div className="upload-form-group">
                    <label htmlFor="tex-name-input">Save As:</label>
                    <input 
                        id="tex-name-input"
                        type="text" 
                        value={texResumeName} 
                        onChange={(e) => setTexResumeName(e.target.value)} 
                        placeholder="e.g., Imported TeX Resume" 
                    />
                </div>
                <button 
                    className={getButtonContent('tex').className}
                    onClick={handleTexUpload} 
                    disabled={!texFile || formStatus.tex.status === 'loading'}
                >
                    {getButtonContent('tex').text}
                </button>
                {formStatus.tex.status === 'error' && <p className="error-message">{formStatus.tex.message}</p>}
            </div>
        </div>
    );
};

export default UploadPage;