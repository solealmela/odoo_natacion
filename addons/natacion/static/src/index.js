document.addEventListener('DOMContentLoaded', async() => {
    const data = await fetch('http://localhost:8069/natacion/api/championship/1').then(response => response.json());
    console.log(data);
    for (const session of data.sesiones) {
        const div = document.createElement('div');
        div.innerHTML = `<h3>${session.nombre}</h3><ul>${session.pruebas.map(p => `<li>${p}</li>`).join('')}</ul>`;
        document.body.appendChild(div);
    }

    document.querySelector('#pagar').addEventListener
    ('click', async() => {
        const response = await fetch('http://localhost:8069/natacion/pagar_quota', {
            method: 'POST',
            body: JSON.stringify({
                id: '1722',
            })
        }).then(response => response.json());
        console.log(response);
    })
});

