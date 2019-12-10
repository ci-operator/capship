**RedRunner**

RedRunner is a microservice utility for executing Ansible playbooks via API as part of a distributed Kubernetes deployment.


A RedRunner Jobs and their Units are created by POSTing to the API a tag and a list of Unit names. Mulitple Jobs can co-exist with the same tag, but each has a unique ID.
PUTting data to a Unit will specify the data_dir containing a project subdirectory full of playbooks.  Operations are triggered by POSTing a playbook filename as the "action" parameter to a Unit.
Each playbook runs in its own thread. 

Generally, each Unit will be named after a microservice component in a cloud application, and the jobs_tag will describe the type of operation performed on all Units within it.


The playbooks and roles provided in `runner/utils` and `runner/components/project` respectively serve as an example one way to use the RedRunner to initialize, trigger, and track the status of playbook operations in tagged RedRunner Job/Unit sets.

To configure and implement this, the ansible playbooks `(restore|backup)-each.yml` are example patterns of pairing two plays, one for configuring units in a job, and another for running and tracking operations in a unit:

1. The Runner defines a Runner Job with Components for each "host" in the next play
- The Runner either finds the latest existing or creates a new Runner Job with the provided 'tag'. 
-- This Job's ID is passed in dynamic inventory vars to hosts in the next play.

2. Operations are triggered for each named component in _that_ Job which matches the component's hostname.
- Operations are run in new RecoveryRunner threads for each member of the play.
- Triggered playbook names follow the conventon: `<action>-<component-name>.yml` or `<action>-each.yml` to target related components.

Job/Component plays are paired in this playbook to designate the _current_ Job ID.
  a. Create Job, or select the last one created, with a specific 'tag'
  b. Trigger Operations to run in _that_ job's Components.


It's noteworthy to recognize that, following this pattern, the Operations's playbooks are triggered in parallel with other operations sharing the same 'action', so an '<action>-<component>.yml' playbook must be accessible for each action/component pair under the _projects_ folder inside the 'data_dir' configured for the Unit. In other words, to implement the 'restart-each.yml', which targets the components 'frontend' and 'backend', you must also implement the 'restart-frontend.yml' and 'restart-backend.yml' and place them inside <data_dir>/projects.  However, if any single component playbook fails, others will continue in their own thread.

Synchronization between components occurs at a Play level, as opposed to at a Task level, and a playbook failure for one component will not affect the run of another component's playbook.  All tasks in each 'action' playbook are performed, for that component, to completion or failure.  As a result, beware that a failure in play won't necessarily prevent a subsequent play from running. 
