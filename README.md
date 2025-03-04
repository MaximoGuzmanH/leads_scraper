# leads_scraper
Scrapers en Python para extraer datos de empresas en Procore Network. links.py obtiene enlaces de perfiles y los guarda en MongoDB. data.py extrae detalles de cada empresa y actualiza los registros. Usa Selenium, BeautifulSoup y pymongo para automatizar el scraping y almacenamiento de datos.

# 🏗️ Procore Network Scraper

Este repositorio contiene dos scrapers para extraer información de empresas del sitio web [Procore Network](https://www.procore.com/network). Se utilizan `Selenium` y `BeautifulSoup` para navegar en la web y obtener datos estructurados de cada empresa.

## 📌 Características

✅ **Scraper de enlaces (`links.py`)**:  
- Navega en Procore Network por estado.
- Aplica filtros de empresas contratistas generales y especializadas.
- Extrae y almacena enlaces en MongoDB.

✅ **Scraper de datos (`data.py`)**:  
- Procesa los enlaces guardados en MongoDB.
- Extrae información clave de cada empresa.
- Ejecuta múltiples solicitudes en paralelo para mayor eficiencia.

## 📦 Requisitos

Antes de ejecutar los scrapers, asegúrate de tener instalados los siguientes paquetes:

```sh
pip install selenium beautifulsoup4 requests pymongo webdriver-manager
```


🚀 Uso
1️⃣ Ejecutar el scraper de enlaces
sh
Copiar
Editar
python links.py
Este proceso recorrerá cada estado en la lista y guardará los enlaces de empresas en MongoDB.

2️⃣ Ejecutar el scraper de datos
sh
Copiar
Editar
python data.py
Este script tomará los enlaces almacenados y extraerá información detallada de cada empresa.

⚙️ Configuración Adicional
🔹 Modo sin cabeza (headless) en Selenium:
El scraper usa headless mode por defecto. Si quieres ver la ejecución en un navegador, edita links.py y comenta la opción:

python
Copiar
Editar
# options.add_argument("--headless")
🔹 Número de hilos en data.py:
Puedes cambiar la cantidad de hilos para mejorar el rendimiento:

python
Copiar
Editar
if __name__ == "__main__":
    scrape_business_data(max_workers=10)  # Ajusta el número según tu CPU
🛠️ Tecnologías Usadas
Selenium: Navegación automatizada
BeautifulSoup: Extracción de datos HTML
Requests: Peticiones HTTP
MongoDB: Almacenamiento de datos
Concurrent Futures: Procesamiento paralelo
📝 Notas
Evita bloqueos: Usa HEADERS en data.py para simular un navegador real.
Manejo de errores: Si una página no carga, el scraper ignora el registro y continúa con el siguiente.
Persistencia de datos: La base de datos MongoDB mantiene el estado de los registros (status=0 para pendientes, status=1 para completados).
📄 Licencia
Este proyecto está disponible bajo la licencia MIT.

📩 ¡Contribuciones y mejoras son bienvenidas! Si encuentras algún problema o tienes una sugerencia, abre un issue en este repositorio.
