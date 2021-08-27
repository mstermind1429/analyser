## **SEO Tools**

#### **Infrastructure**

Web Application of SEO Tools is run on Django and 
Django REST Framework. Configuration of the project can be found at `analyser/settings.py`.<br>

All of the main tools can be found at `app/tools/` and each of them is represented as an API View. You can access the urls of APIs at `app/rest_urls.py`.
There is also a management command `python manage.py lighthouse` for running Google Lighthouse with required input file. File should be located at `/reports/urls_lighthouse.csv` and should contain 3 columns:
- URL
- Keyword
- Position

#### **Starting an application**

Install required modules for Python virtual environment<br>
`pip install -r requirements.txt`<br>

If there is an error `ImportError`, you can manually install missed packages with<br> 
`pip install package_name`

Create PostgreSQL Table **"analyser"**

Edit configurations and set env variables for: <br>
`SECRET_KEY` (Django Secret Key)<br>
`EMAIL_USERNAME` (Gmail username for sending an email)<br>
`EMAIL_PASSWORD` (Gmail password for sending an email)<br>
`DB_USERNAME` (PostgreSQL username)<br>
`DB_PASSWORD` (PostgreSQL password)<br>

Migrate to database<br>
`python manage.py migrate`<br>

Create a superuser<br>
`python manage.py createsuperuser`

Run application with<br>
`python manage.py runserver`

Now you can visit `127.0.0.1:8000` or `localhost:8000`
and `localhost:8000/admin` for accessing admin panel.


