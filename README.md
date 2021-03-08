# What is this app?
This is a Python script that runs a query on JIRA server and generate Web Graphiz text that can be used to produce dependency graph. Often in project planning, tasks have dependency, hence often require specific order of execution.  [Web Graphviz](http://www.webgraphviz.com) gives visual presentation using a special syntax for data input. This Python script generate text of same syntax that enables graphviz drawing. It can also help with some adhoc calculation, such as estimate of total effort of tasks that are still to be done, or those that are in progress. Generally it produces somewhat more useful output then a plan JIRA query output can produce.

# How to use
The script can be run with Python 3.6 at the minimum. Had been tested using Python 3.8. Dependencies must be provided (as seen in requirement.txt). There is Dockerfile as well, if we wish to run the script using docker.

This script connects to JIRA server (basic auth) using the following environment variables - JIRA_USER, JIRA_PASSWORD and JIRA_URL (with this last one being defaulted to https://jira.ec2.local)

There are 3 other arguments, read in order:
* input_search_term - A query term that the script will use for fetching from JIRA. This query term is supposed to be that used by JIRA search tool.
* black_list - A comma separated list of IDs of tasks, that are to be excluded from the report (Sometime, there are "awkward" task that JIRA seemingly have difficulties to filter them out, so we can jsut give an explicit list of items we don't want to see)
* todo - A flag, set to "todo" if we want the script to produce a kind of summary report at the end (in addition to Graphiz text)

# Usage
## Using venv
```
python3 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt
export JIRA_USER=...
export JIRA_PASSWORD=...
python3 jira_report <input_search_term> <black_list> <todo>
```
## Using Docker
```
docker login <docker_hub>
docker build . -t python:jira
docker tag python:jira <docker_hub>/sparrow/python:jira
docker push <docker_hub>/sparrow/python:jira
docker run --env JIRA_USER --env JIRA_PASSWORD -it --rm python:jira jira_report.py <input_search_term> <black_list> <todo>
```