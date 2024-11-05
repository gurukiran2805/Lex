import jenkins
import time
from spellchecker import SpellChecker

# Jenkins connection details
jenkins_url = "http://your-jenkins-url:8080"
jenkins_username = "your-username"
jenkins_token = "your-api-token"
jenkins_server = jenkins.Jenkins(jenkins_url, username=jenkins_username, password=jenkins_token)

# Initialize spell checker
spell = SpellChecker()

# Known job types for spellchecking
known_job_types = ["Freestyle", "Pipeline", "Multibranch"]

def lex_response(message, session_attributes=None):
    """Format response to Lex V2 format."""
    return {
        'sessionState': {
            'dialogAction': {'type': 'ElicitIntent'},
            'intent': {'name': 'JenkinsOperations', 'state': 'Fulfilled'},
            'sessionAttributes': session_attributes or {}
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

def spell_check_and_suggest(word, known_words):
    """Check for spelling mistakes and suggest corrections."""
    best_match = spell.correction(word)
    if best_match not in known_words:
        return f"Did you mean '{best_match}'?"
    return None

def check_job_exists(job_name):
    """Check if a Jenkins job exists."""
    try:
        jenkins_server.get_job_info(job_name)
        return True  # Job exists
    except jenkins.NotFoundException:
        return False  # Job does not exist

def create_job(job_name, job_type, github_url=None):
    """Create a Jenkins job based on the job type."""
    if job_type == "Freestyle":
        config_xml = '''<project><builders/><publishers/><buildWrappers/></project>'''
    elif job_type == "Pipeline":
        config_xml = '''<flow-definition plugin="workflow-job@2.40">
                            <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
                                <script>pipeline { agent any; stages { stage('Build') { steps { echo 'Building...'; } } } </script>
                            </definition>
                        </flow-definition>'''
    elif job_type == "Multibranch" and github_url:
        config_xml = f'''<flow-definition plugin="workflow-multibranch@2.21">
                            <branchSources>
                                <jenkins.branch.BranchSource>
                                    <source class="jenkins.plugins.git.GitSCMSource">
                                        <url>{github_url}</url>
                                    </source>
                                </jenkins.branch.BranchSource>
                            </branchSources>
                        </flow-definition>'''
    else:
        return f"Oops! Something went wrong. The job type '{job_type}' or missing GitHub URL for Multibranch is invalid."

    try:
        jenkins_server.create_job(job_name, config_xml)
        return f"Yay! Jenkins job '{job_name}' of type '{job_type}' has been created successfully. You're on fire!"
    except jenkins.JenkinsException as e:
        return f"Oops, there was an issue creating the job: {str(e)}. Can you double-check the details?"

def build_jenkins_job(job_name):
    """Trigger a Jenkins job build and check the build status."""
    try:
        build_number = jenkins_server.build_job(job_name)
        
        while True:
            build_info = jenkins_server.get_build_info(job_name, build_number)
            if build_info['building']:
                time.sleep(60)  # Wait 1 minute before checking again
            else:
                build_status = build_info['result']
                build_url = f"{jenkins_url}/job/{job_name}/{build_number}/"
                if build_status == 'SUCCESS':
                    return f"All done! The build was a success 🎉. Check it out here: {build_url}. Nice work!"
                elif build_status == 'FAILURE':
                    return f"Oh no 😞, the build failed. Don't worry, you can check the details here: {build_url}. Let's figure it out!"
                else:
                    return f"Build finished with status: {build_status}. Here’s the link: {build_url}. Let's move on to the next task!"
    except jenkins.JenkinsException as e:
        return f"Something went wrong while trying to build the job. Sorry about that! Here's the error: {str(e)}"

def list_jobs():
    """List all Jenkins jobs."""
    try:
        jobs = jenkins_server.get_jobs()
        job_names = [job['name'] for job in jobs]
        return f"Here are the available Jenkins jobs: {', '.join(job_names)}. Let me know which one you’d like to work with."
    except jenkins.JenkinsException as e:
        return f"Oops! I couldn't retrieve the list of jobs. Here's the error: {str(e)}."

def delete_job(job_name):
    """Delete a Jenkins job."""
    if check_job_exists(job_name):
        try:
            jenkins_server.delete_job(job_name)
            return f"Job '{job_name}' has been successfully deleted. It’s gone, but not forgotten!"
        except jenkins.JenkinsException as e:
            return f"Sorry, I ran into an issue while trying to delete the job '{job_name}'. Here's the error: {str(e)}"
    else:
        return f"Hey, I couldn’t find a job named '{job_name}' to delete. Could you double-check the name?"

def get_job_info(job_name):
    """Get Jenkins job information."""
    if check_job_exists(job_name):
        try:
            job_info = jenkins_server.get_job_info(job_name)
            return f"Here’s the info for job '{job_name}': {job_info}. Let me know if you need more details!"
        except jenkins.JenkinsException as e:
            return f"Sorry, I couldn’t retrieve job information for '{job_name}'. Here's the error: {str(e)}"
    else:
        return f"Job '{job_name}' doesn’t seem to exist. Double-check the name, please!"

def get_last_build_info(job_name):
    """Get the last build status and URL."""
    if check_job_exists(job_name):
        try:
            last_build_number = jenkins_server.get_job_info(job_name)['lastBuild']['number']
            build_info = jenkins_server.get_build_info(job_name, last_build_number)
            build_status = build_info['result']
            build_url = f"{jenkins_url}/job/{job_name}/{last_build_number}/"
            return f"The last build for job '{job_name}' has status: {build_status}. Check out the details here: {build_url}."
        except jenkins.JenkinsException as e:
            return f"Oops, there was an issue retrieving the last build info for job '{job_name}'. Here's the error: {str(e)}"
    else:
        return f"Job '{job_name}' doesn’t seem to exist. Can you double-check the name?"

def get_build_logs(job_name):
    """Get logs for the last build of a Jenkins job."""
    if check_job_exists(job_name):
        try:
            last_build_number = jenkins_server.get_job_info(job_name)['lastBuild']['number']
            build_logs = jenkins_server.get_build_console_output(job_name, last_build_number)
            return f"Here are the logs for the last build of job '{job_name}':\n{build_logs[:1000]}... (truncated). Let me know if you'd like to see more!"
        except jenkins.JenkinsException as e:
            return f"Sorry, I couldn’t fetch the logs for the last build of job '{job_name}'. Here's the error: {str(e)}"
    else:
        return f"Job '{job_name}' doesn’t seem to exist. Double-check the name, please!"

def handle_lex_request(event):
    """Handle Lex request and perform Jenkins operations."""
    intent_name = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']
    
    # Extract job details from Lex slots
    job_name = slots.get('JobName', {}).get('value', {}).get('interpretedValue')
    job_type = slots.get('JobType', {}).get('value', {}).get('interpretedValue')
    github_url = slots.get('GitHubRepoUrl', {}).get('value', {}).get('interpretedValue')
    confirmation = slots.get('Confirmation', {}).get('value', {}).get('interpretedValue')
    
    session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})

    # Handle spell check only if relevant fields are provided
    if job_name:
        correction = spell_check_and_suggest(job_name, [])
        if correction:
            return lex_response(f"Oops! I think you might have a typo in the job name '{job_name}'. {correction} Let me know if you meant something else!", session_attributes)

    if job_type:
        correction = spell_check_and_suggest(job_type, known_job_types)
        if correction:
            return lex_response(f"Hmm, looks like there's a typo in the job type '{job_type}'. {correction} Let me know if I got that wrong!", session_attributes)

    # Handle job creation and building
    if intent_name == "CreateJenkinsJob":
        if not job_name:
            return lex_response("Hey! I need a job name to create the Jenkins job. What should I call it?", session_attributes)
        if not job_type:
            return lex_response("Got it! Please tell me what type of Jenkins job it should be (Freestyle, Pipeline, or Multibranch)?", session_attributes)
        if job_type == "Multibranch" and not github_url:
            return lex_response("For a Multibranch job, I need a GitHub repository URL. Can you provide it?", session_attributes)
        
        # Proceed to create job
        response = create_job(job_name, job_type, github_url)
        return lex_response(response, session_attributes)

    # Handle other operations
    if intent_name == "BuildJenkinsJob":
        if not job_name:
            return lex_response("I need the job name to trigger a build. Can you tell me which job you'd like to build?", session_attributes)
        
        # Proceed to build job
        response = build_jenkins_job(job_name)
        return lex_response(response, session_attributes)

    if intent_name == "ListJenkinsJobs":
        response = list_jobs()
        return lex_response(response, session_attributes)

    if intent_name == "DeleteJenkinsJob":
        if not job_name:
            return lex_response("Please provide the name of the Jenkins job you’d like to delete.", session_attributes)
        
        response = delete_job(job_name)
        return lex_response(response, session_attributes)

    if intent_name == "GetJobInfo":
        if not job_name:
            return lex_response("I need the name of the job to get details. What job do you want to know about?", session_attributes)
        
        response = get_job_info(job_name)
        return lex_response(response, session_attributes)

    if intent_name == "GetBuildLogs":
        if not job_name:
            return lex_response("Please provide the name of the Jenkins job to fetch build logs.", session_attributes)
        
        response = get_build_logs(job_name)
        return lex_response(response, session_attributes)

    return lex_response("I’m sorry, I didn’t quite understand that. Can you please rephrase?", session_attributes)

def lambda_handler(event, context):
    """Lambda function handler."""
    return handle_lex_request(event)
