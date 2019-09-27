#!/usr/bin/python
#TODO: limit maximum number of concurrent runners (!!!)

import ansible_runner
import logging
import json
import re

default_data_dir='runner'
runners={}

logger = logging.getLogger(__name__)

ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
def escape_ansi(line):
    return ansi_escape.sub('', line)

class Runner():
    def __init__(self, **kwargs):
        global runners
        self.op_id = kwargs['op_id']
        self.data_dir = kwargs.get('data_dir') or default_data_dir #FIXME
        self.status = 'ready'
        self.task = None
        self.runner = None
        self.runnerconfig = None
        self.stdout = None
        self.handler = kwargs.get('handler') or None
        self.run_handler = kwargs.get('run_handler') or None
        self.done_handler = kwargs.get('done_handler') or None
        runners[self.op_id] = self
        self.interface = { 'op_id': self.op_id,
                           'data_dir': self.data_dir,
                           'task': self.task,
                           'status': self.status,
                           'stdout': self.stdout }

    def start(self, project, playbook):
        logger.debug("STARTING %s: %s, %s", str(self), project, playbook)
        running = False

        self.runnerconfig = ansible_runner.run_async(
            private_data_dir = self.data_dir, 
            playbook = playbook, 
            event_handler = self.handle_event,
            status_handler = self.handle_status,
            finished_callback = self.finish,
            ident = str(self.op_id),
            quiet = True )
            # Note: config files override some of of these
            # project_dir = project,
            # json_mode = True
            # ident = str(self.op_id) + '_' + playbook[:-4],

        logger.info("private_data_dir: %s, project: %s, playbook: %s, ident: %s", self.data_dir, project, playbook, str(self.op_id))

        try:
            job = ansible_runner.run(config=self.runnerconfig)
            logger.debug("job: %s", str(job))
            self.runner = job[1]
            self.stdout = self.runner.stdout
            running = True
        except ValueError as e:
            logger.error("%s", str(e))
            if self.handler:  #run_handler or done_handler?
                self.handler( 
                    { 'error': True,
                      'op_id': self.op_id, 
                      'stdout': str(e) } )
        finally:
            return running

    #TODO: Expose this endpoint somehow
    def get_facts(host='localhost'):
        return self.runner.get_fact_cache(host)

    def handle_event(self, e):
        event=e['event']
        logger.debug("#### TASK %s EVENT: %s ####: %s", self.op_id, event, str(e))
        if event == 'playbook_on_start':
            logger.info("Runner %s Starting playbook: %s", self.op_id, e['event_data']['playbook'])
            if self.done_handler:
                self.done_handler( 
                    {'op_id': self.op_id, 
                     'status': self.status } )
        elif event == 'runner_on_start':
            logger.debug("Task executing: %s", e['event_data']['task_path'])
            self.task = e['event_data']['task']
            if self.run_handler:
                self.run_handler( 
                    { 'op_id': self.op_id,
                      'task': self.task } )
        elif event in ['runner_on_ok', 
                       'runner_item_on_ok',
                       'runner_on_skipped',
                       'runner_on_failed',
                       'verbose', #<-- TODO: handle differently?
                       'playbook_on_include', #<-- Has no stdout
                       'playbook_on_stats', #<-- Check for stdout
                       'playbook_on_play_start', 
                       'playbook_on_task_start']:
            logger.debug("Event Data: %s", str(e.get('event_data',None)))
            self.task = None
            if self.run_handler:
                logger.debug("Handling '%s': %s", str(event), str(e))
                self.run_handler( 
                    { 'op_id': self.op_id,
                      'stdout': escape_ansi(e.get('stdout')),
                      'task': '' } )
        elif event in ['playbook_on_no_hosts_remaining', 'runner_retry', 'runner_item_on_skipped']:
            pass # TODO: handle this stdout too
        else:
            logger.warn("Unhandled Event '%s': %s", str(event), str(e))

    def handle_status(self, s, **kwargs):
        logger.debug("Runner %s Status: %s", s['runner_ident'], s['status'])
        self.status = s['status']
        if self.run_handler:
            self.run_handler( 
                {'op_id': s['runner_ident'], 
                 'stdout': (escape_ansi(s.get('stdout') or '')) or (escape_ansi(s.get('stderr') or '' )),
                 'status': s['status']} )

    def finish(self, runner):
        logger.info("Runner %s DONE! Status: %s", self.op_id, runner.status)
        if self.done_handler:
            finalstatus = {
                'op_id': self.op_id,
                'status': self.status }
            if runner.stdout:
                finalstatus.update( {'stdout': escape_ansi(''.join(list(runner.stdout))) } )
            self.done_handler( finalstatus )

    def poll(self, op_id):
        return runners.get('op_id') or None

    def toJSON(self):
        return json.dumps(self.interface, indent=2, sort_keys=True, default=str )

    def __repr__(self):
        return self.toJSON()

    def __str__(self):
        return str(self.interface)
