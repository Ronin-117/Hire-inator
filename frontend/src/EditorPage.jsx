import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { auth } from './firebaseConfig';

const EditorPage = () => {
    const { resumeId } = useParams(); // Get the resume ID from the URL

    // State
    const [resumeData, setResumeData] = useState(null);
    const [pdfUrl, setPdfUrl] = useState('');
    const [chatInput, setChatInput] = useState('');

    const [isLoading, setIsLoading] = useState(true);
    const [isRefining, setIsRefining] = useState(false);
    const [error, setError] = useState('');

    // Function to fetch the latest PDF blob and update the viewer
    const refreshPdf = async () => {
        if (!auth.currentUser) return;
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/download/`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!response.ok) throw new Error('Failed to compile and fetch PDF.');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            setPdfUrl(url);
        } catch (err) {
            console.error(err);
            setError("Could not generate PDF preview. There might be a compilation error in the LaTeX code.");
        }
    };

    // Initial data load effect
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
                
                // Now that we have the data, generate the initial PDF preview
                await refreshPdf();
                
            } catch (err) {
                console.error(err);
                setError(err.message);
            }
            setIsLoading(false);
        };
        loadInitialData();
    }, [resumeId]); // Re-run if the resumeId changes

    const handleRefine = async () => {
        if (!chatInput.trim() || !resumeData) return;
        
        setIsRefining(true);
        setError('');
        
        try {
            const token = await auth.currentUser.getIdToken();
            const formData = new FormData();
            // We pass the new instruction and the original JD for context
            formData.append('instruction', chatInput);
            formData.append('job_description', resumeData.jobDescription || ''); // Assuming JD is saved with resume


            const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/refine/`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to refine resume.');

            // Success! Clear the chat and refresh the PDF
            setChatInput('');
            await refreshPdf();

        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setIsRefining(false);
        }
    };

    if (isLoading) return <h1>Generating Initial PDF Preview...</h1>;

    return (
        <div>
            <Link to="/profile">← Back to Profile</Link>
            <h1>Resume Editor: {resumeData?.resumeName}</h1>
            
            {error && <p style={{ color: 'red' }}><strong>Error:</strong> {error}</p>}
            
            <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
                {/* PDF Viewer Column */}
                <div style={{ flex: 1, border: '1px solid #ccc' }}>
                    {pdfUrl ? (
                        <iframe src={pdfUrl} width="100%" height="800px" title="Resume Preview"></iframe>
                    ) : (
                        <p>Loading Preview...</p>
                    )}
                </div>

                {/* Chat and Controls Column */}
                <div style={{ flex: 1 }}>
                    <h3>Refine with AI</h3>
                    <p>Give the AI further instructions to modify your resume.</p>
                    <textarea 
                        rows="10" 
                        style={{ width: '90%' }}
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="e.g., 'Make the summary more concise' or 'Change the first bullet point under Tech Solutions to highlight data processing.'"
                    />
                    <br/>
                    <button onClick={handleRefine} disabled={isRefining}>
                        {isRefining ? 'Updating...' : 'Send Instruction'}
                    </button>
                    <hr/>
                    <h3>Final Actions</h3>
                    <button>Save to Profile</button>
                    <a href={pdfUrl} download={`${resumeData?.resumeName}.pdf`}>
                        <button disabled={!pdfUrl}>Download Current PDF</button>
                    </a>
                </div>
            </div>
        </div>
    );
};

export default EditorPage;