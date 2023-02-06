# streamsets
streamsets - ci-cd pipeline

Pre-requisites:
  Job template should be created for the pipeline file. 
 
 Command:
  `python app.py -env qa -cid $CRED_ID -token $TOKEN -job_template_name dev_job`

developer either commits the entire pipeline file (file obtained from export pipeline) into pipelines/ directory or commit_id and commit_label be present in the config.yaml file

The secrets [credential and token] are stored in github actions secret [ CRED_ID, TOKEN].

This uses streamsets python sdk

Any pushes to `main` branch triggers the pipeline. 

pipelines folder should contain only the latest pipeline [if config.yaml is not used]

First identifty the jobs that are running from the job_template that has the environment tag.

The purpose of pipeline file is just to read pipeline commit id and pipeline commmit label.

Once we have this information, we update the job_template to the input commit id and input commit label.

Then run the jobs based on the updated job_template. 
