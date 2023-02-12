# streamsets
streamsets - ci-cd pipeline

Pre-requisites:
  Pipeline id should be provided in config.yaml
 
 Command:
  `python app.py -env qa -cid $CRED_ID -token $TOKEN -job_template_name dev_job`

developer either commits the entire pipeline file (file obtained from export pipeline) into pipelines/ directory or commit_id and commit_label be present in the config.yaml file

The secrets [credential and token] are stored in github actions secret [ CRED_ID, TOKEN].

This uses streamsets python sdk

Any pushes to `main` branch triggers the pipeline. 

pipelines folder should contain only the latest pipeline [if config.yaml is not used]

The pipeline checks if there is any job template present for the pipeline. If not, it creates a job_template.

if job_template exists, update the job_template to use the latest version of pipeline.

The pipeline then checks for any running jobs that are created from job_template.

If jobs are present, update the job to reflect the new version of job_template

Then run the jobs based on the updated job_template. 
