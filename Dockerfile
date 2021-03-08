FROM python:3

# Add any OS packages required (e.g. odbc drivers)

COPY *.py requirements.txt **/* ./

# Install dependencies:
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
