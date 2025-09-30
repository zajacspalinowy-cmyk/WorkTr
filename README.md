# WorkTr

Prosty system do nadzoru projektów (Django).

## Wymagania
- Python 3.11+
- pip

## Szybki start
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # utwórz własne sekrety
python manage.py migrate
python manage.py runserver
