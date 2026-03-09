document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('http://localhost:8069/natacion/api/championship/1');
        const data = await response.json();
        
        console.log("Datos recibidos de Odoo:", data);

       for (const session of data.sesiones) {
            const div = document.createElement('div');
            div.className = "session-card";
            div.innerHTML = `
                <h3>${session.nombre}</h3>
                <ul>
                    ${session.pruebas.map(p => `<li>${p}</li>`).join('')}
                </ul>
            `;
            document.getElementById('lista-sesiones').appendChild(div);
        }
    } catch (error) {
        console.error("Error cargando el campeonato:", error);
    }

    const botonPagar = document.querySelector('#pagar');
    if (botonPagar) {
        botonPagar.addEventListener('click', async () => {
            console.log("Enviando pago...");
            
            try {
                const response = await fetch('http://localhost:8069/natacion/pagar_quota', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        params: {
                            id: '1722'
                        }
                    })
                });

                const result = await response.json();
                
                console.log("Respuesta del pago:", result.result);
                alert(result.result.message);
                
            } catch (error) {
                console.error("Error en la petición de pago:", error);
            }
        });
    }
});