import os
import time
import json
import argparse
import datetime
import yaml
from streamsets.sdk import ControlHub
from streamsets.sdk.exceptions import JobRunnerError


def options():
    parser = argparse.ArgumentParser(description='Streamsets CI/CD script')
    parser.add_argument('-env', default='dev', choices=['qa', 'prod', 'dev'], help='Environment to push the Pipeline',
                        required=True, dest='env', metavar='environment')
    parser.add_argument('-cid', help='Credential ID', required=True)
    parser.add_argument('-token', help='Token', required=True)
    args = parser.parse_args()
    return args

def get_commit_id_from_config():
    result = ()
    with open("config.yaml") as stream:
        dt = yaml.safe_load(stream)
        result = dt['commit_id'], dt['commit_version']
    return  result

def stop_and_delete_job(job):
    retry_counts = 0
    while retry_counts < 4:
        try:
            retry_counts += 1
            sch.stop_job(job)
        except TimeoutError:
            time.sleep(60)
        except JobRunnerError as e:

            break
        else:
            response = sch.get_current_job_status(job=job).response
            if response.status_code == 200:

                if response.json()['status'].upper() not in ('ACTIVE', 'DEACTIVATING'):
                    break
                else:
                    sch.delete_job(job)
def deploy_pipeline(environment, job_template_name):

    # assumption data/qa.json, data/prod.json
    data_collector = sch.data_collectors.get(reported_labels=[environment])
    file_path = f"pipelines/{max(os.listdir('pipelines'))}"
    data = json.load(open(file_path))


    run_time_parameter_json = f'data/{environment}.json'
    with open(run_time_parameter_json) as f:
        run_time_parameters = json.load(f)
        print(run_time_parameters)

    job_template = sch.jobs.get(job_name=job_template_name, job_template=True)

    print(job_template.job_id)

    # filter the jobs that are created from i/p job_template that has {env} tags
    all_jobs = sch.jobs.get_all(job_template=False,
                                    template_job_id=job_template.job_id, raw_job_tags=[environment])
    for job in all_jobs:
        stop_and_delete_job(job)

    # create the new job
    if os.path.isfile('config.yaml'):
        commit_id, pipeline_commit_label = get_commit_id_from_config()
    else:
        commit_id = data['pipelineConfig']['metadata']['dpm.pipeline.commit.id']
        pipeline_commit_label = data['pipelineConfig']['metadata']['dpm.pipeline.version']
    job_template.data_collector_labels = [environment]
    job_template.commit_id = commit_id
    job_template.commit_label = f"v{pipeline_commit_label}"
    sch.update_job(job_template)

    sch.start_job_template(job_template=job_template,
                           name=f'{job_template_name}-{environment}-{datetime.datetime.now()}',
                           raw_job_tags=[environment], runtime_parameters=run_time_parameters)


args = options()

# sch = ControlHub(credential_id=args.cid, token=args.token)
# deploy_pipeline(environment=args.env, job_template_name=args.job_template_name)
print(os.environ)