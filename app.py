import argparse
import datetime
import json

import yaml

from streamsets.sdk import ControlHub


def options():
    parser = argparse.ArgumentParser(description='Streamsets CI/CD script')
    parser.add_argument('-env', default='dev', choices=['qa', 'prod', 'dev'], help='Environment to push the Pipeline',
                        required=True, dest='env', metavar='environment')
    parser.add_argument('-cid', help='Credential ID', required=True)
    parser.add_argument('-token', help='Token', required=True)
    args = parser.parse_args()
    return args

def read_config():
    with open("config.yaml") as stream:
        dt = yaml.safe_load(stream)
    return  dt

def deploy_pipeline(environment):

    run_time_parameter_json = f'data/{environment}.json'
    with open(run_time_parameter_json) as f:
        run_time_parameters = json.load(f)

    config = read_config()
    pipeline_id = config['pipeline_id']

    pipeline = sch.pipelines.get(pipeline_id=pipeline_id)
    pipeline_commits = pipeline.commits
    pipeline_commits.sort(reverse=True, key=lambda x:x.version)
    latest_commit = pipeline_commits[0]
    job_template_name = f'Job Template SDK - {pipeline.name}'
    job_builder = sch.get_job_builder()
    try:
        job_template = sch.jobs.get(pipeline_id=pipeline_id, job_template=True)
    except ValueError:
        job_template = job_builder.build(job_template_name,
                        pipeline=pipeline, job_template=True, runtime_parameters=run_time_parameters)
        sch.add_job(job_template)
    else:
        job_template = sch.jobs.get(pipeline_id=pipeline_id, job_template=True)
    
    job_template.data_collector_labels = config['data_collector_labels'][environment]
    job_template.commit_id = latest_commit.commit_id
    job_template.commit_label = f"v{latest_commit.version}"
    for key,value in config['job_template_args'].items():
        job_template.__setattr__(key, value)
    
    sch.update_job(job_template)

    # filter the jobs that are created from i/p job_template that has {env} tags
    all_jobs = sch.jobs.get_all(job_template=False,
                                    template_job_id=job_template.job_id, raw_job_tags=[environment])

    if all_jobs:
        sch.upgrade_job(*all_jobs)

    sch.start_job_template(job_template=job_template,
                           name=f'{job_template_name}-{environment}-{datetime.datetime.now()}',
                           raw_job_tags=[environment], runtime_parameters=run_time_parameters)


args = options()
cid = args.cid
token = args.token
# cid = '6380daa2-4417-4c01-a0a0-29bcefe7912c'
# token = """eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzIjoiN2YwY2FiMjgwNmM5Y2EyMjU0ZWRhMTY3NGI0ZmMzNGExYzFhODhjN2MxZDlhZjk4YTgxYzdlZTM1NjZhZTY4ZTgzMjU0MjY2MGZiMjg5Y2YzNTFhMzg4NzcwOTM2ZDcyNWFiNWE2ODkxNWViZjUwYjk0MjY5NTIwNDYzZTJlZGEiLCJ2IjoxLCJpc3MiOiJuYTAxIiwianRpIjoiNjM4MGRhYTItNDQxNy00YzAxLWEwYTAtMjliY2VmZTc5MTJjIiwibyI6IjNmZGMzNjYxLThiZDMtMTFlZC1hNGQ0LTA3NjU2M2I1OTljOSJ9."""
sch = ControlHub(credential_id=cid, token=token)
deploy_pipeline(environment=args.env)