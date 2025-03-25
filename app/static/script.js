document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const downloadBtn = document.getElementById('downloadBtn');
    const progressSection = document.querySelector('.progress-section');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    const resultsDiv = document.getElementById('results');

    downloadBtn.addEventListener('click', async () => {
        const urls = urlInput.value.split('\n').filter(url => url.trim());
        
        if (urls.length === 0) {
            alert('Please enter at least one YouTube URL');
            return;
        }

        // Show progress section
        progressSection.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Processing videos...';
        resultsDiv.innerHTML = '';
        downloadBtn.disabled = true;

        try {
            const response = await fetch('/api/transcript', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ urls }),
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data.results);
            } else {
                throw new Error(data.error || 'Failed to fetch transcripts');
            }
        } catch (error) {
            resultsDiv.innerHTML = `
                <div class="result-item">
                    <h3>Error</h3>
                    <p class="error-message">${error.message}</p>
                </div>
            `;
        } finally {
            // Hide progress section
            progressSection.style.display = 'none';
            downloadBtn.disabled = false;
        }
    });

    function displayResults(results) {
        resultsDiv.innerHTML = '';
        
        results.forEach((result, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            if (result.error) {
                resultItem.innerHTML = `
                    <h3>Error Processing: ${result.title}</h3>
                    <p class="error-message">${result.error}</p>
                `;
            } else {
                const blob = new Blob([result.transcript], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                
                resultItem.innerHTML = `
                    <h3>${result.title}</h3>
                    <a href="${url}" download="${result.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_transcript.txt">
                        Download Transcript
                    </a>
                `;
            }

            resultsDiv.appendChild(resultItem);
        });

        // Update progress bar
        progressFill.style.width = '100%';
        progressText.textContent = 'Processing complete!';
    }
}); 