import re

from jira import JIRA
# import networkx as nx

NEW_LINE = '\\n'
SPACE = ' '

COLORS = {
    "Open": "AliceBlue",
    "Reopened": "AliceBlue",

    "Ready for Review": "lightpink",
    "Ready for Development": "lightyellow",

    "In Development": "aquamarine",
    "Code Review": "lightblue",
    "Formal Testing in Progress": "lightblue",
    "Closed": "PaleGreen"
}

# Set this to zero to disable further following links
MAX_JIRA_SEARCH_DEPTH = 3


def __search_jira_recursively(server, search_term, blacklist, vertices, edges, recursive_depth):

    if recursive_depth <= 0:
        return

    recursive_depth -= 1

    issues = server.search_issues(search_term)
    followup_search = ''
    for issue in issues:
        if in_black_list(issue.key, blacklist):
            continue
        this_issue = wrap_text('%s %s' %(issue.key, issue.fields.summary))

        # This is a hack. There is no neat way to extract estimate points at this stage, so this is only a guess
        # It may not work for another JIRA instance

        estimate = -1.0
        if hasattr(issue.fields, 'customfield_10003'):
            estimate = issue.fields.customfield_10003

        vertices.add((this_issue, issue.fields.status.name, estimate)) # Add status & story points

        for link in issue.fields.issuelinks:
            if hasattr(link, "outwardIssue") and not in_black_list(link.outwardIssue.key, blacklist):
                update_with_link(link, "outwardIssue", vertices, edges, this_issue)
                # This is where there is a potential performance improvement
                # Build up the search term in stead of going one by one like this
                # if followup_search is not '':
                if followup_search:
                    followup_search += ' or '
                followup_search += 'key="%s"' % link.outwardIssue.key

            if hasattr(link, "inwardIssue") and not in_black_list(link.inwardIssue.key, blacklist):
                update_with_link(link, "inwardIssue", vertices, edges, this_issue)

    # if followup_search is not '':
    if followup_search and recursive_depth > 0:
        __search_jira_recursively(server, followup_search, blacklist, vertices, edges, recursive_depth)


def run_report(server, search_term, blacklist):
    # This function performs JIRA search and build up a DiGraph object for dependency between JIRA issues.
    # it runs recursive search, taking an initial DiGraph object (vertices and edges) and keeps accumulating to
    # the vertices and edges when these are detected from JIRA relationship.
    # Dependency between issues is presented as a collection (or more exactly - a set) of tuples, each tuple is
    # a pair - where the first item is meant to be the predecessor and the second item is the dependent card.
    # vertices store individual issues with their status (Done / In progress, etc)
    # edges store the order of issues (before-after relationships)
    
    # param "search_term": any valid JQL Jira Search query
    # param "blacklist": excluding certain issues from final report (when too hard to be specified by search term)
    # param "recursive_depth": A limit on following with JIRA issue do after (to avoid infinite loop)

    # return  "vertices" and "edges": the initial and final DiGraph object produced by this report
    the_vertices = set()
    the_edges = set()
    __search_jira_recursively(server, search_term, blacklist, the_vertices, the_edges, MAX_JIRA_SEARCH_DEPTH)
    return the_vertices, the_edges


def color_coded_status(status):
    return COLORS[status] if status in COLORS.keys() else "orange"


def wrap_text(input_text, wrap_size=3):
    words = input_text.strip().replace("'", SPACE).replace('"', SPACE).split(SPACE)
    output_text = ''
    count = 0
    while count < len(words):
        if (count - 1) % wrap_size == 0:
            output_text += NEW_LINE
        else:
            output_text += SPACE
        output_text += words[count]
        count += 1
    return output_text.strip()


def get_jira_connection():
    jira_url='https://jira.ec2.local'
    import os
    try:
        username = os.environ['JIRA_USER']
        password = os.environ['JIRA_PASSWORD']
        jira_url = os.environ.get('JIRA_URL', jira_url)
        return JIRA(options={'server': jira_url, 'verify':False}, basic_auth=(username, password))
    except KeyError as e:
        print(f'ERROR: Cannot connect to {jira_url}! Please define JIRA_USER, JIRA_PASSWORD, JIRA_URL')
        exit(1)


def in_black_list(issue_summary, black_list):
    for item in black_list:
        if item in issue_summary:
            return True
    return False


def update_with_link(link, link_type_name, current_vertices, current_edges, current_issue):
    if hasattr(link, link_type_name):
        linked_object = getattr(link,link_type_name)
        key = linked_object.key
        summary = linked_object.fields.summary
        status = linked_object.fields.status.name
        linked_text = wrap_text('%s %s' % (key, summary))
        story_points = 0.01
        current_vertices.add((linked_text, status, story_points))

        if link_type_name == "outwardIssue":
            current_edges.add((current_issue, linked_text))
        elif link_type_name == "inwardIssue":
            current_edges.add((linked_text, current_issue))


def generate_graphviz_text(vertices, edges):
    graphviz_text = 'digraph G { node [fontname = "Verdana", style = "filled"];\n'
    for v in vertices:
        graphviz_text += '"%s" [color="%s"];\n' %(v[0], color_coded_status(v[1]))
    for pair in edges:
        graphviz_text += '"%s" -> "%s";\n' % (pair[0], pair[1])
    graphviz_text += '}\n'
    return graphviz_text


def draw_dependency_diagram(edges):
    # dependency to networkx (which ultimately needs 'dot' is broken after I install python 3.7 to use with AWS
    # and after I install python 3.8 for system - To be sorted out
#     G = nx.DiGraph()
#     G.add_edges_from(edges)
#     p=nx.drawing.nx_pydot.to_pydot(G)
#     p.write_png("dependency.png")
    pass


def read_input_args():
    import sys
    if len(sys.argv) >= 2:
        input_search_term = sys.argv[1]
        black_list = []
        todo = None
        if len(sys.argv) >= 3:
            black_list = [x.strip(' ') for x in sys.argv[2].split(',')]
            if len(sys.argv) >= 4:
                todo = sys.argv[3]
        return input_search_term, black_list, todo
    else:
        raise EnvironmentError('Insufficient number of inputs arguments, see help!')


def print_planning_report(jira_issues):
    print("TODO: List of items still to be done")
    todo_points = 0
    for v in jira_issues:
        if v[1] in ["Open", "Reopened", "Ready for Review", "Ready for Development"]: # and (v[2] and v[2] > 0.5):
            eco_number = re.search('ECO\\-\d+', v[0], re.IGNORECASE)
            if eco_number:
                eco = eco_number.group(0)
                estimate = v[2] if v[2] else -1.01
                if estimate > 1.0:
                    print('https://jira.ec2.local/browse/%s : %.2f, %s' % (eco, estimate, v[0].replace('\\n', ' ')))
                    todo_points += estimate
    print('todo_points: %.2f' % todo_points)

    print("TODO: List of items still to be done but not yet estimated")
    unestimated_points = 0
    for v in jira_issues:
        if v[1] in ["Open", "Reopened", "Ready for Review", "Ready for Development"]: # and (v[2] and v[2] > 0.5):
            eco_number = re.search('ECO\\-\d+', v[0], re.IGNORECASE)
            if eco_number:
                eco = eco_number.group(0)
                estimate = v[2] if v[2] else -1.01
                if estimate < 1.0:
                    print('https://jira.ec2.local/browse/%s : %.2f, %s' % (eco, estimate, v[0].replace('\\n', ' ')))
                    unestimated_points += estimate
    print('unestimated_points: %.2f' % unestimated_points)

    print("Currently in progress - in dev / review / testing")
    indev_points = 0
    for v in jira_issues:
        eco_number = re.search('ECO\\-\d+', v[0], re.IGNORECASE)
        if eco_number:
            eco = eco_number.group(0)
            if v[1] in ["In Development", "Code Review", "Testing", "Test Review", "Test Automation"]:
                if eco_number:
                    estimate = v[2] if v[2] else -1.01
                    if estimate > 0:
                        print('https://jira.ec2.local/browse/%s : %.2f, %s' % (eco, estimate, v[0].replace('\\n', ' ')))
                        indev_points += estimate
            # else:
            #     print(f'{eco} - {v[1]}')
    print('indev_points: %.2f' % indev_points)


if __name__ == '__main__':
    query, black_list, todo = read_input_args()
    jira_server = get_jira_connection()
    jira_issues, jira_links = run_report(jira_server, query, black_list)

    draw_dependency_diagram(jira_links)

    print('\n\nhttp://www.webgraphviz.com/\n\n')
    graphviz_text = generate_graphviz_text(jira_issues, jira_links)
    print(graphviz_text)
    #This bit cannot work in a docker container
    #import pyperclip
    #pyperclip.copy(graphviz_text)

    if todo:
        print_planning_report(jira_issues)


