== RedRunner

RedRunner is a microservice utility for executing Ansible playbooks via API as part of a distributed Kubernetes deployment.

By convention, each RedRunner Job is created with a tag to designate the type of Operations performed in it. Playbook-running Operations are run in their own thread, with each Operation performed inside a named Unit, and there may be many Units in a Job. Generally, each Unit will be named after a microservice component in a cloud application.  All playbook Operations are performed by POSTing a playbook filename as the "action" parameter to a Unit.

To configure and implement this, the ansible playbooks `(restore|backup)-each.yml` are provided in the utils as an example pattern of pairing two plays, one for configuring units in a job, and another for running and tracking operations in a unit:

1. The Runner defines a Runner Job with Components for each "host" in the next play
- The Runner either finds the latest or creates a new Runner Job with a 'tag'. 
-- This Job's ID is passed in dynamic inventory vars to hosts in the next play.

2. Operations are triggered for each named component in _that_ Job which matches the component's hostname.
- Operations are run in new RecoveryRunner threads for each member of the play.
- Triggered playbook names follow the format: `<action>-<component-name>.yml` (with 'each' targeting all components)

Job/Component plays are paired in this playbook to designate the _current_ Job ID.
  a. Create Job, or select the last one created, with a specific 'tag'
  b. Trigger Operations to run in _that_ job's Components.


It's noteworthy to recognize that, following this pattern, the Operations's playbooks are triggered in parallel with other operations sharing the same 'action', so an '<action>-<component>.yml' playbook must be accessible for each action/component pair under the _projects_ folder inside the 'data_dir' configured for the Unit. 

Syncronization between components occurs at a Play level, as opposed to at a Task level, and a playbook failure for one component will not affect the run of another component's playbook.  All tasks in each 'action' playbook are performed, for that component, to completion or failure.

The playbooks and roles provided in `runner/utils' and 'runner/components/project' respectively serve as an example how to use the RedRunner to initialize, trigger, and track the status of playbook operations in a tagged RedRunner Job.
