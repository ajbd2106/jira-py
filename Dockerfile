FROM python:3

# Add any OS packages required (e.g. odbc drivers)

# Copy files
# Question - is this something people do often? Just copy all things to the root of docker container?
# Is "./" being understood as the root of docker container?
# JIRA accessing jira_ini - Check with Ilya to see how that is done for the release cut activities
COPY *.py requirements.txt **/* ./

# Install dependencies:
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
