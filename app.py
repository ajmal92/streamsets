import os
import time
import json
import argparse
import datetime
from streamsets.sdk import ControlHub
from streamsets.sdk.exceptions import JobRunnerError


def options():
    parser = argparse.ArgumentParser(description='Streamsets CI/CD script')
    parser.add_argument('-env', default='dev', choices=['qa', 'prod', 'dev'], help='Environment to push the Pipeline',
                        required=True, dest='env', metavar='environment')
    parser.add_argument('-cid', help='Credential ID', required=True)
    parser.add_argument('-token', help='Token', required=True)
    parser.add_argument('-job_template_name', help='job template name', required=True)
    args = parser.parse_args()
    return args


def deploy_pipeline(environment, job_template_name, credential_id, token):
    sch = ControlHub(credential_id=credential_id, token=token)
    # assumption data/qa.json, data/prod.json
    data_collector = sch.data_collectors.get(reported_labels=[environment])
    file_path = f"pipelines/{max(os.listdir('pipelines'))}"
    data = json.load(open(file_path))
    commit_id = data['pipelineConfig']['metadata']['dpm.pipeline.commit.id']
    pipeline_commit_label = data['pipelineConfig']['metadata']['dpm.pipeline.version']

    run_time_parameter_json = f'data/{environment}.json'
    with open(run_time_parameter_json) as f:
        run_time_parameters = json.load(f)
        print(run_time_parameters)

    job_template = sch.jobs.get(job_name=job_template_name, job_template=True)

    print(job_template.job_id)

    # filter the jobs that are created from i/p job_template that has {env} tags
    all_jobs = sch.jobs.get_all(job_template=False,
                                    template_job_id=job_template.job_id, raw_job_tags=[environment])
    retry_counts = 0
    for job in all_jobs:
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

    # create the new job
    job_template.data_collector_labels = [environment]
    job_template.commit_id = commit_id
    job_template.commit_label = f"v{pipeline_commit_label}"
    sch.update_job(job_template)

    sch.start_job_template(job_template=job_template,
                           name=f'{job_template_name}-{environment}-{datetime.datetime.now()}',
                           raw_job_tags=[environment], runtime_parameters=run_time_parameters)


args = options()

# credential_id = '6380daa2-4417-4c01-a0a0-29bcefe7912c'
# token ="""eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzIjoiMzIwN2MyYWU1MmY0OTNiYjExNzczNWZmYjM2NzkxYWVmNzQ0MjBlY2E5MGFiZTVlYTM0YjllZTgxYTBkY2QzYjM4ZTIzYThiMWZmNmI3NWY4OThiMWE4NGQyNGFiYmIwODkwNzljZjFhOTA2N2I2MTAxOTFlYmVjNDBmN2E3MGMiLCJ2IjoxLCJpc3MiOiJuYTAxIiwianRpIjoiNjM4MGRhYTItNDQxNy00YzAxLWEwYTAtMjliY2VmZTc5MTJjIiwibyI6IjNmZGMzNjYxLThiZDMtMTFlZC1hNGQ0LTA3NjU2M2I1OTljOSJ9."""
deploy_pipeline(environment=args.env, job_template_name=args.job_template_name, credential_id=args.cid,
                token=args.token)