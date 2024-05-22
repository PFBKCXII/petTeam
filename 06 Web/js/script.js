function isValidYouTubeUrl(url) {
    const regex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
    return regex.test(url);
}

function extractVideoID(url) {
    const regex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
}

function analyze() {
    const url = document.getElementById('youtubeUrl').value;
    if (!isValidYouTubeUrl(url)) {
        alert('Por favor, introduce una URL válida de YouTube.');
        return;
    }

    const videoID = extractVideoID(url);
    if (!videoID) {
        alert('URL de YouTube no válida.');
        return;
    }

    document.getElementById('videoContainer').innerHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${videoID}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('results').innerHTML = ''; // Limpiar resultados anteriores

    // Reemplaza con la URL de tu función de Google Cloud
    fetch('https://us-central1-hatespeechdetector-420911.cloudfunctions.net/youtube', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ videoID: videoID })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('spinner').style.display = 'none';
        displayResults(data);
    })
    .catch(error => {
        document.getElementById('spinner').style.display = 'none';
        alert('Error al analizar el video.');
        console.error('Error:', error);
    });
}

function displayResults(data) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = `
        <h2>Comentarios del vídeo</h2>
        <p>ID del video: ${data.video_id}</p>
        <ul>
            ${data.results.map(result => `
                <li>
                    <p><strong>Autor:</strong> ${result.author}</p>
                    <p>${result.comment}</p>
                </li>
            `).join('')}
        </ul>
    `;
}

function clearPage() {
    document.getElementById('youtubeUrl').value = '';
    document.getElementById('videoContainer').innerHTML = '';
    document.getElementById('spinner').style.display = 'none';
    document.getElementById('results').innerHTML = '';
}

function openTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    tabs.forEach(tab => tab.style.display = 'none');
    buttons.forEach(button => button.classList.remove('active'));

    document.getElementById(tabId).style.display = 'block';
    document.querySelector(`.tab-button[onclick="openTab('${tabId}')"]`).classList.add('active');
}
