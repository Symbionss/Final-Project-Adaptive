# Migrate SDN Monitoring to Django with Topology Visualization

This plan details the migration of the existing Flask application to a robust Django project, while explicitly introducing a visually stunning dynamic network topology visualization that integrates with the Ryu controller.

## Proposed Changes

### Configuration and Setup

#### [MODIFY] [Dockerfile](file:///c:/Users/Thinkpad%20X390/Documents/Random%20Coding/Final%20-%20Project/sdn_monitoring/project/Dockerfile)
- Change CMD to run the Django development server instead of `app.py`.

#### [NEW] [requirements.txt](file:///c:/Users/Thinkpad%20X390/Documents/Random%20Coding/Final%20-%20Project/sdn_monitoring/project/requirements.txt)
- Define standard dependencies required: `Django` and `requests`.

### Django Migration

#### [NEW] Django Project & App Configuration
- Create a new Django project and a dedicated app (e.g., `sdn_app`).
- Set up standard `settings.py`, `urls.py`, and `wsgi.py/asgi.py`. 
- Ensure `RYU_API` parses from `os.environ` identical to the Flask version.

#### [NEW] [views.py](file:///c:/Users/Thinkpad%20X390/Documents/Random%20Coding/Final%20-%20Project/sdn_monitoring/project/sdn_app/views.py)
- Port the `/` route to return the `index.html` template.
- Port `/block_ip` and `/unblock_ip` handlers.
- **New Feature**: Add an endpoint `/api/topology` that acts as a proxy, gathering node and link data from Ryu controller REST APIs (`/v1.0/topology/switches`, `/v1.0/topology/links`) and normalizing it so the frontend can easily read it.

### Frontend Overhaul

#### [MODIFY] [index.html](file:///c:/Users/Thinkpad%20X390/Documents/Random%20Coding/Final%20-%20Project/sdn_monitoring/project/templates/index.html) (Will be moved or updated according to Django's template engine configuration)
- **State-of-the-art Design**: Upgrade aesthetics to a modern, dark-mode glassmorphism theme using high-quality Google Fonts (e.g., *Inter* or *Outfit*) to provide a premium feel as requested.
- **Topology Visualization**: Integrate the [Vis-Network](https://visjs.org/) library to draw interactive, physics-based network graphs of switches and hosts.
- **Preserved Features**: Maintain the control panel for blocking/unblocking IPs and the Grafana iFrame integration, styled to match the new dynamic environment.
- Add JS logic to fetch data from the new `/api/topology` Django view and populate the Vis-Network chart.

#### [DELETE] [app.py](file:///c:/Users/Thinkpad%20X390/Documents/Random%20Coding/Final%20-%20Project/sdn_monitoring/project/app.py)
- The legacy Flask entry point will be discarded once Django handles the routing.

## User Review Required

> [!IMPORTANT]
> - Do you want the Django project initialized directly inside the `project/` directory? (I will configure the Dockerfile to run `python manage.py runserver 0.0.0.0:5000` to maintain compatibility with `docker-compose.yaml`).
> - The new topology visualizer will proxy data through Django instead of communicating directly with Ryu via JS to circumvent parsing complexity and CORS. Let me know if that is acceptable.

## Verification Plan

### Automated / Manual Tests
- Restart the Docker container `docker-compose restart flask` or rebuild it if necessary (`docker-compose build flask`).
- Open the dashboard in a browser and verify the "WOW" aesthetics and dynamic topology chart.
- Attempt to block and unblock an IP checking both functionality and visual response.
